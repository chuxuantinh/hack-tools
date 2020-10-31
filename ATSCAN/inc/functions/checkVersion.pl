#!/usr/bin/perl
use strict;
use warnings;
use FindBin '$Bin';
use File::Path;
## Copy@right Alisam Technology see License.txt

## CHECK VERSION AND UPDATE
our ($scriptUrl, $script_bac, $script, $logUrl, $scriptv, $userSetting, $scriptInstall, $scriptComplInstall, $scriptCompletion, $scriptbash, $readme,
     $uplog, $fulldate, @userSetting, @ErrT, @DT, @c, @OTHERS, @AUTH, @ZT);
print $c[4]."[!] $OTHERS[20]\n";
my ($same, $response)=compareme();
if ($same eq "yes") {   
  print $c[3]."$DT[6]\n";
}else{
  if (-e $userSetting) {
    print $c[10]."[!] $ZT[0] ";
    open my $dle, '<', $userSetting or nochmod($userSetting, "");
    chomp(@userSetting = <$dle>);
    close $dle;
    cc();
  }
    
  my ($r, $ht, $stats, $serverh)=getHtml($scriptUrl, "");
  if (!$r->is_success) { print "\n"; dd(); exit(); }
    
  print $c[10]."[!] $ZT[1] ";
  open (LE, '>', $script) or nochmod($script, "exit");
  print LE $r->content; close(LE);
  cc();
    
  print $c[10];
  system("git clone https://github.com/AlisamTechnology/ATSCAN.git $Bin/atscan_update");
  if (!-d "$Bin/atscan_update") { print "\n"; dd(); exit(); }
    
  print $c[10]."[!] $ZT[2] ";
  system "sudo cp -r $Bin/atscan_update/inc $Bin";
  if (!-d "$Bin/inc") { bb(); exit(); }
  else{ cc(); }
    
  my @f=("README.md", "License.txt");
  for my $f(@f) {
    print $c[10]."[!] $ZT[5] $f to $readme/... ";
    system "sudo cp -r $Bin/atscan_update/$f /usr/share/doc/atscan/";
    if (!-e "/usr/share/doc/atscan/$f") { bb(); }
    else{ cc(); }
  }
    
  print $c[10]."[!] $ZT[4] ";
  open (FILE, '>>', $scriptv) or nochmod($scriptv, "");
  print FILE "\n"; close(FILE);
  cc();    
    
  if (-e $scriptbash) {
    if (-d $scriptCompletion) {
      my $scbs="$scriptCompletion/atscan";        
      unlink $scbs if -e $scbs;
      print $c[10]."[!] $ZT[5] $scriptComplInstall to $scriptCompletion/... ";
      system "sudo cp $scriptComplInstall $scriptCompletion/";
      if (!-e "$scriptCompletion/atscan") { bb(); }
      else{ cc(); }
    }
  }
  
  print $c[10]."[!] $ZT[9] ";
  open (MN, '>', $uplog) or nochmod($uplog, "");
  print MN "$fulldate"; close(MN);
  sleep(1);
  cc();
  
  unlink $userSetting if -e $userSetting;   
  if (@userSetting) {
    print $c[10]."[!] $ZT[6] ";
    for my $spss(@userSetting) {
      open (FE, '>>', $userSetting) or nochmod($userSetting, "");
      print FE "$spss\n"; close(FE);
    }
    cc();
  }

  print $c[10]."[!] $ZT[7] ";
  system "rm -rf $Bin/atscan_update";
  if (!-d "$Bin/atscan_update") { cc(); }
  else{ bb(); }
    
  my @unlinks=($scriptComplInstall, $scriptInstall, $Bin."/README.md", $Bin."/License.txt", $script_bac);
  for my $unlink(@unlinks) {
    print $c[10]."[!] $ZT[8] $unlink... ";
    unlink $unlink if -e $unlink;
    if (!-e $unlink) { cc(); }      
  }
  sleep(1);
  print $c[3]."[!] $DT[7]\n";
  print "$c[10]\n".$response->content.""; 
  if (substr($0, -3) ne '.pl') {
    my $zs=$script.".pl";
    unlink $zs if -e $zs or nochmod($zs, "");
  }
}

1;
