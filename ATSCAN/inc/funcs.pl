#!/usr/bin/perl
use strict;
use warnings;
use FindBin '$Bin';
use POSIX qw(strftime);
## Copy@right Alisam Technology see License.txt

## FUNCTS
our ($payloads, $exploit, $data, $mlevel, $dork, $Target, $V_RANG, $noQuery, $mdom, $replace, $with, $full, $unique, $ifinurl, $pat2, $limit, $port, $output, $ifend, $ipUrl, $noinfo, $V_IP);
our (@aTscans, @data, @userArraysList, @exploits, @dorks, @aTsearch, @aTcopy, @aTtargets, @c, @OTHERS, @DS, @DT, @TT, @proxies, @ErrT);

## PRINT FILES 
sub printFile {
  my ($File, $context)=@_;
  open (FILE, '>>', $File); print FILE "$context\n"; close(FILE);
}

## CHECK EMPTY FORDERS
sub is_folder_empty {
  my $dirname = $_[0];
  opendir(my $dh, $dirname);
  return scalar(grep { $_ ne "." && $_ ne ".." } readdir($dh)) == 0;
}

## USER PRE-CONFIGURATION
our($userSetting, $proxy, $prandom, $password, $brandom, $mrandom, $zone, $motor, $nobanner, $beep, $timeout, $dateupdate, $activeUconf, $freq, $method, $checkVersion, $get, $post);
sub checkSetting {
  my $object=$_[0];
  my @ans;
  open(F2, $userSetting);
  while (my $l=<F2>) {
    chomp $l;
    if ($l=~/$object\s(.*)\s$object/) {
      @ans=split(" ", $l);
    }    
  }
  close(F2);
  return $ans[1];
}

## BUILT ARRAYS
sub buildArraysLists {
  my $buildArrays=$_[0];
  my @buildArrays=();
  if (-e $buildArrays) {
    open (UAL, $buildArrays);
    while (my $buildArray=<UAL>) {
      chomp $buildArray;
      push @buildArrays, $buildArray;
    }
  }else{
    $buildArrays=~s/\s+$//g;
    $buildArrays=~s/^\[OTHER]//g;
    @buildArrays=split /\[OTHER\]/, $buildArrays;
  }
  return @buildArrays;
}

## BUILD PROXIES ARRAY
sub getProx {
  my $getProx=$_[0];
  if ($getProx=~/:/) { @proxies=split / /, $getProx; }
  else{ @proxies=buildArraysLists($getProx); }
  return @proxies;
}

## DELETE USER SETTING
sub deletSetting {
  our (@configuration, @LI2, $userSetting);
  my $val=$_[0];
  for my $lines(@configuration) {
    if ($lines!~/^$val\s(.*)/) {
      push @LI2, $lines;
    }
  }
  unlink $userSetting; @configuration=();
  for my $lines2(@LI2) { printFile($userSetting, $lines2); }
}

## CHECK USER CONFIGURATION
$activeUconf=checkSetting("config");
$password=checkSetting("password");

if ($activeUconf) {
  $proxy=checkSetting("proxy") if !defined $proxy;
  $prandom=checkSetting("proxy-random") if !defined $prandom;
  $payloads=checkSetting("payload") if !defined $payloads;
  $brandom=checkSetting("b-random") if !defined $brandom;
  $mrandom=checkSetting("m-random") if !defined $mrandom;  
  $mlevel=checkSetting("level") if !defined $mlevel;
  $method=checkSetting("method") if !defined $get and !defined $post;
  $zone=checkSetting("zone");
  $motor=checkSetting("engine") if !defined $motor;
  $nobanner=checkSetting("nobanner") if !defined $nobanner;
  $noinfo=checkSetting("noinfo") if !defined $noinfo;
  $beep=checkSetting("beep") if !defined $beep;
  $ifend=checkSetting("ifend") if !defined $ifend;
  $unique=checkSetting("unique") if !defined $unique;
  $timeout=checkSetting("timeout") if !defined $timeout;
  $dateupdate=checkSetting("update");
  $freq=checkSetting("freq") if !defined $freq;
}
## SET PROXY
if (defined $proxy || $proxy) { @proxies=getProx($proxy); }
if (defined $prandom || $prandom) { @proxies=getProx($prandom); }

## USER ARRAYS
if (defined $payloads || $payloads) { @userArraysList=buildArraysLists($payloads); }

## EXPLOITS ARRAYS
if (defined $exploit) { @exploits=buildArraysLists($exploit); }

## MAX POSITIVE SCAN RESULTS
## Chnage for more positive scans!!
$limit="500" if !defined $limit;

## SET RANDOM FREQUENCY START TIME
sub get_frequecy {
  my $now = strftime "%H%M%S", localtime;
  return $now;
}
our $start=get_frequecy();

## CURRENT PROXY
sub get_psx {
  if (scalar(grep { defined $_} @proxies)>0) {
    my $fin = 0;
    my $psx;
    while(!$fin) {
      $psx=$proxies[rand @proxies];
      if ($psx) { $fin = 1; }
    }
    return $psx;
  }
}

## SET CURRENT PROXY
our $psx=get_psx();

## BROWSER
our (@sys, @vary, @systems);
use IO::Socket::INET;
use LWP::UserAgent;
use HTTP::Cookies;
use HTTP::Request;
binmode STDOUT, ":utf8";
for my $sys(@sys) {
  for my $vary(@vary) {
    my $ag="$sys) $vary";
    push @systems, $ag;
  }
}

our ($system, $agent, $ua);

## TIMEOUT
sub get_timeout {
  my $time;
  if (defined $timeout || $timeout) { $time=$timeout; }
  else{ $time=10; }
  return $time;
}

## HEADERS
our $headers;
if (defined $headers) {
  $headers=~s/\:/\=\>/g;
  $headers=~s/^\[OTHER\]//g;
  $headers=~s/\[OTHER\]/\,/g;
}else{ $headers=""; }

## SET PROXY
$agent="Mozilla/5.0 (".$systems[rand @systems];
$ua=LWP::UserAgent->new( agent => $agent, $headers, cookie_jar => HTTP::Cookies->new());
$ua->default_header('Accept' => ('text/html'));
$ua->env_proxy;
$timeout=get_timeout();
$ua->timeout($timeout);
if ($proxy || $prandom || defined $proxy || defined $prandom) {  
  $ua->proxy([qw/ http https ftp ftps /] => $psx); $ua->cookie_jar({ });
}

## MEKE FREQUENCY RANDOM 
sub make_freq {
  if ($freq || defined $freq) {
    my $stop=get_frequecy();
    if ($freq || defined $freq) {
      my $def=$stop - $start; 
      if ($def >= $freq) {
        if (defined $brandom || $brandom) { getNewAgent(); }
        if (defined $prandom || $prandom) { newIdentity(); }
      }
    }
  }
}

## GET CURRENT IDENTITY
sub get_ipAddress {
  my $ipadress;
  my $r=$ua->get($ipUrl);
  if ($r->is_success) {
    if ($r->content=~m/$V_IP/g) { $ipadress="$1"; }
  }
  return $ipadress;
}

## GET NEW PROXY
sub getNewproxy {
  my $currentpsx=$psx;
  my $newpsx;
  my $fi=0;
  while(!$fi) {
    $newpsx=$proxies[rand @proxies];
    if ($newpsx ne $psx) {
      $fi=1;
    }
  }
  return $newpsx;
}

## RENEW IDENTITY
sub newIdentity {
  if (defined $prandom || $prandom) {
    if ($psx=~/(localhost|127.0.0.1)/) {
      my $add=get_ipAddress();
      my $ff=0;
      while (!$ff) {
        system("[ -z 'pidof tor' ] || pidof tor | xargs sudo kill -HUP -1;");
        my $newadd=get_ipAddress();
        if ($newadd ne $add) { $ff=1; }
      }
    }else{
      my $psx=getNewproxy(); UA();
    }
  }
}

## RENEW AGENT
sub getNewAgent {
  my $currentagent=$agent;
  my $fin=0;
  while (!$fin) {
    $agent="Mozilla/5.0 (".$systems[rand @systems];
    if ($currentagent ne $agent) {
      $fin=1;
    }   
  }
  $ua=LWP::UserAgent->new( agent => $agent, cookie_jar => HTTP::Cookies->new());
}

## CHECK CONNECTION
sub testConnection {
  print $c[4]."[!] $DT[31]\n";
  if ($proxy || $prandom || defined $proxy || defined $prandom) { print $c[4]."[!] $ErrT[20] [$psx].. "; }    
  my $respons=$ua->get($ipUrl);
  if (!$respons->is_success) {
    if ($proxy || $prandom || defined $proxy || defined $prandom) { print "\n"; }
    print $c[2]."[!] $DT[11]\n[!] $DT[10]\n".$c[4]."[!] $ErrT[23]\n"; logoff();
  }else{
    if ($proxy || $prandom || defined $proxy || defined $prandom) { print $c[3]."[!] OK!\n"; ltak(); }
  }
}

## UA
sub UA {
  $psx=$proxies[rand @proxies];
  $ua->proxy([qw/ http https ftp ftps /] => $psx); $ua->cookie_jar({ });
}

## DATA ARRAYS
if (defined $data) {
  my @data_full=buildArraysLists($data);
  my @data44;
  my $f_data;
  for my $d_d(@data_full) {
    if ($d_d=~/\[DATAFILE\]/) {
      $d_d=~s/\[DATAFILE\]/\[DATA\]/g;      
      $f_data=$d_d;  
      $d_d=~s/\s+$//g;       
      $d_d=~s/^\[DATA\]//g; 
      $d_d=~s/\[DATA\]/ ATSCAN /g; 
      my @data7=split("ATSCAN", $d_d); 
      for my $data7(@data7) {    
        my @data3=split(":", $data7);
        $data3[1]=~s/ //g;
        if (-e $data3[1]) {
          $f_data=~s/ATSCAN/\[DATA\]/g;
          open(F5, $data3[1]) or advise_no_file($data3[1]);
          while (my $f=<F5>) {
            chomp $f;
            $f_data=~s/$data3[1]/$f/g;
            $f_data=~s/ //g;
            push @data44, $f_data;
            $f_data=~s/$f/$data3[1]/g;
          }
          push @data, @data44;
        }
      }
    }else{
      push @data, $data;
    }
  }
}

## DORKS & TARGETS ARRAYS
if (defined $mlevel) {
  if (defined $dork) { @dorks=buildArraysLists($dork); }
  elsif (defined $Target) {
    if (($Target=~/$V_RANG/)&&($1<=255 && $2<=255 && $3<=255 && $4<=255 && $5<=255 && $6<=255 && $7<=255 && $8<=255)) { 
      my $startIp=$1.".".$2.".".$3.".".$4;
      my $endIp=$5.".".$6.".".$7.".".$8;  
      my (@ip,@newIp,$i,$newIp,$j,$k,$l);
      @ip=split(/\./,$startIp);
      for($i=$ip[0];$i<=$5;$i++) { 
	    $ip[0]=0 if($i == $5);
        for($j=$ip[1];$j<=$6;$j++) { 
          $ip[1]=0 if($j == $6);
          for($k=$ip[2];$k<=$7;$k++) { 
            $ip[2]=0 if($k == $7);
            for($l=$ip[3];$l<=$8;$l++) { 
              $ip[3]=0 if($l == $8);
              $newIp=join('.',$i,$j,$k,$l);
              $newIp="ip%3A".$newIp;             
              push @dorks, $newIp;
            }
	      }
	    }
      }
    }else{
      @dorks=buildArraysLists($Target);
    }
  }
}else{
  if (defined $Target) {
    if (($Target=~/$V_RANG/)&&($1<=255 && $2<=255 && $3<=255 && $4<=255 && $5<=255 && $6<=255 && $7<=255 && $8<=255)) { 
      my $startIp=$1.".".$2.".".$3.".".$4;
      my $endIp=$5.".".$6.".".$7.".".$8;
      my (@ip,@newIp,$i,$newIp,$j,$k,$l);
      @ip=split(/\./,$startIp);
      for($i=$ip[0];$i<=$5;$i++) { 
	    $ip[0]=0 if($i == $5);
        for($j=$ip[1];$j<=$6;$j++) { 
          $ip[1]=0 if($j == $6);
          for($k=$ip[2];$k<=$7;$k++) { 
            $ip[2]=0 if($k == $7);
            for($l=$ip[3];$l<=$8;$l++) { 
              $ip[3]=0 if($l == $8);
              $newIp=join('.',$i,$j,$k,$l);
              push @aTsearch, $newIp;
            }
          }
	    }
      }
    }else{ @aTsearch=buildArraysLists($Target); }
  }
}

## TIMER
sub timer { our $date; print "[$date]"; }

## CHECK VERSION LOG
sub compareme {
  my ($same);
  our ($logUrl, $script_bac, $scriptv);
  my ($response, $html, $status, $serverheader)=getHtml($logUrl, "");
  if ($response->is_success) {
    unlink $script_bac if -e $script_bac;
    printFile($script_bac, $response->content);    
    use File::Compare;      
    if (compare($script_bac, $scriptv) == 0) {
      $same="yes";
      unlink $script_bac;
    }else{ $same="no"; }
  }else{ $same="yes"; }
  return ($same, $response);
}

## RETURN NEGATIVE SCAN
sub negative { ltak(); print $c[4]."[!] $DT[1]\n"; }

## DESCLAIMER
sub desclaimer {
  our ($nobanner, $checkVersion);
  if (defined $nobanner) { mtak(); ptak(); }
  print $c[10]."  $OTHERS[11] \n  $OTHERS[12]  \n  $OTHERS[13] \n"; 
  if (defined $dork || defined $Target) {
    our $uplog;
    if (-e $uplog) { require "$Bin/inc/conf/upad.pl"; }
  }
  mtak(); ptak();
  if (defined $dork || defined $Target || defined $checkVersion) {    
    testConnection();
  }
}

## BGN SCAN TITLE
sub scanTitleBgn { print $c[11]."[!] "; timer(); print " ::: $DS[67] "; }

## END SCAN TITLE
sub scanTitleEnd { print $c[11]." $DS[4] :::\n"; ptak(); }

## GET CLEAN TARGETS DOMAINE
sub IfDup { my @aTsearch=(); @aTsearch=@aTtargets; @aTtargets=(); }

## GET DOMMAINE AND REMOVE PROTOCOL
sub removeDupNoProtocol {
  for my $URL(@aTsearch) { $URL=removeProtocol($URL); $URL=~s/www.//s; saveCopy($URL); }
  my @aTsearch=checkDuplicate(@aTsearch); IfDup();
}

## MEKE SEARCH COPY
sub makeCopy { my @aTcopy=(); push @aTcopy, @aTsearch; }

## RESTAURE SEARCH COPY
sub restaureSearch { my @aTsearch=(); push @aTsearch, @aTcopy; @aTcopy=(); }

## REMOVE DUPLICATE DOMAINES WPAFD/JOOMRFI/SUBDOMAINS/ADMIN
sub removeDupDom { 
  makeCopy();
  for my $URL(@aTsearch) { $URL=removeProtocol($URL); $URL=~s/\/.*//s; $URL=checkUrlSchema($URL); saveCopy($URL); }
  my @aTsearch=checkDuplicate(@aTsearch); IfDup();
}

## SAVE NON DUPLICATE DOMAINES
sub saveCopy { my $URL=$_[0]; push @aTtargets, $URL; }

## REMOVE DUPLICATE RESULTS
sub checkDuplicate { 
  my @AS=@_;
  my @AS2;
  for my $as(@AS) { $as=~s/(\%27|\<|\>|\%25|\')(.*)//ig; push @AS2, $as; }
  my %seen;
  @AS2=grep{ not $seen{$_}++ } @_;
  return @AS2;
}

## REMOVE URLS PROTOCOL
sub removeProtocol { 
  my $URL=$_[0];
  my %replace=('http://' => '', 'https://'=>'', 'ftp://'=>'', 'ftps://'=>'', 'socks(4|5)?://'=>'');
  $URL=~s/$_/$replace{ $_}/g for keys %replace;
  return $URL;
}

## REMOVE QUERY STRING
sub removeQuery { 
  my $URL=$_[0];
  $URL=removeProtocol($URL);
  $URL=~s/=.*/=/g;
  $URL=checkUrlSchema($URL);	
  return $URL;
}

## CHECK TARGETS FOR REPLACE OPTION
sub control {
  my $URL=$_[0];
  if (defined $noQuery) {
    $URL=removeQuery($URL);
  }
  if (defined $mdom) {               
	$URL=removeProtocol($URL);
    $URL=~s/\/.*//s;
  }
  if (defined $replace) {
	if (index($URL, $replace) != -1) {
      $URL=~s/$replace(.*)/$replace/g if defined $full; 
      $URL=~s/$replace/$with/ig;
    }
  }    
  $URL=checkUrlSchema($URL);
  return $URL;
}

## CLEAN URL
sub cleanURL {
  my $URL=$_[0];
  my %replace=( 'http://' => '', 'https://' => '', 'www.' => '', 'ftp://' => '', 'ftps://' => '');
  $URL=~s/$_/$replace{ $_}/g for keys %replace;
  $URL=~s/\/.*//s;
  return $URL;
}

## CHECK URL PARTS
sub checkUrlSchema { 
  my $URL=$_[0];
  if ($URL!~/(https?|ftp):\/\//) { $URL="http://$URL"; }; return $URL;
}

## GET FILTERS
sub checkFilters {
  my $dorkToCheeck=$_[0];
  my $dmn="";
  if ($dorkToCheeck=~/(site:(.*)\+|\+site:(.*))/) {
    $dmn=$1;
    $dmn=~s/\+//g;
    $dmn=~s/site:/\./g;
  }
  $dorkToCheeck=~s/:\s/:/g;
  $dorkToCheeck=~s/$pat2//g;
  return ($dorkToCheeck);
}

## GET FILTRED URLS
sub filterUr {
  my ($URL, $dorkToCheeck)=@_;
  if (defined $unique || $unique) {
    if (index($URL, $dorkToCheeck) != -1) { $URL=$URL; }else{ $URL=""; }
  }
  if (defined $ifinurl) {
    if (index($URL, $ifinurl) != -1) { $URL=$URL; }else{ $URL=""; }
  }
  return $URL;
}

## VALIDATE URL PARTS
sub validateURL {
  my $vURL=$_[0];
  $vURL=cleanURL($vURL);
  return $vURL if $vURL=~/([a-zA-Z0-9\-\_]\.)?([a-zA-Z0-9\-\_]\.)[a-zA-Z]/;
}

## CHECK SCANS HEADERS
sub checkHeaders {
  my ($ct, $dt, $et)=@_;
  if ($ct) { scanTitleBgn(); }
  if ($dt) { removeDupDom(); }
  if ($et) { removeDupNoProtocol(); }
}

## COUNT RESULTS
sub OO { my $o=scalar(grep { defined $_} @aTscans); return $o; }


## END SCAN PROCESS
sub subfin {
  our $ifend;
  print $c[2]."[!] "; timer(); print " $DT[3]!\n";
  if (defined $ifend || $ifend) { print chr(7); }
}

## COUNT SCAN RESULTS
sub countResultLists {
  my $o=OO();
  if ($o==$limit) { print $c[4]."[!] $DT[34] ($limit)!\n"; }
  print $c[3]."[!] ".$o." $DT[4]\n";
}

## SEARCH REGEX FILTER
sub doRegex { 
  my $searchRegex=$_[0];
  for my $URL(@aTsearch) {
    if ($URL=~/$searchRegex/) { saveCopy($URL); }
  }
}

## EXTRAT INFO PROCESS SCAN
sub checkExtraInfo { 
  my $URL3=$_[0];
  my $ip;
  if (!defined $port) {
    $URL3=cleanURL($URL3);
    use Socket;
    $ip=inet_aton($URL3);
  }
  return $ip;
}

## BUILT POSITIVE SCAN RESULTS LIST
sub saveme { 
  my ($URL1, $sep)=@_;
  my $o=OO();
  if ($o<$limit) {
    push @aTscans, $URL1;
    if (defined $output) { printFile("$output", " $URL1"); }
  }
}

## SCAN TITLE
sub title { 
  if (defined $output) { my $SCAN_TITLE=$_[0];  printFile("$output", "="x30 ."\n$SCAN_TITLE\n"."="x30); }
}

## CHECK IF THERE MORE SCANS TO DO
our ($WpSites, $JoomSites, $xss, $lfi, $JoomRfi, $WpAfd, $adminPage, $subdomain, $mupload, $mzip, $searchIps, $eMails, $regex, $command);
our @z=($WpSites, $JoomSites, $xss, $lfi, $JoomRfi, $WpAfd, $adminPage, $subdomain, $mupload, $mzip, $searchIps, $eMails, $regex, $port, $data, $command);
sub getK {
  our @z;
  my ($x, $y)=@_; my $k=0; splice @z, $x, $y;
  for (@z) { if (defined $_) { $k++; } } return $k;  
}

## UPDATE
sub nochmod {
  my ($path, $action)=@_;
  sleep(1);
  print $c[2]."[!] Couldn't have write permitions: $path !\n";
  if ($action) { logoff(); } 
}
sub cc { sleep(1); print $c[3]."OK\n"; }
sub bb { sleep(1); print $c[4]."Failed!\n"; }
sub dd { sleep(1); print $c[4]."[!] $DT[8]\n"; }

1;
