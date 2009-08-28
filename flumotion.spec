%define gstpy 0.7.94
%define pygtk 2.4.0
%define release %mkrel 1

Name:           flumotion
Version: 0.6.0
Release: %release
Summary:        Flumotion - the Fluendo Streaming Server

Group:          System/Servers
License:	GPL
URL:            http://www.flumotion.net/
Source:         http://www.flumotion.net/src/flumotion/%{name}-%{version}.tar.bz2
Source1:	flumotion-make-dummy-cert.bz2
Patch:	flumotion-0.5.1-init.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

Requires:	python >= 2.3
Requires:	gstreamer0.10-plugins-good
Requires:	gstreamer0.10-python >= %gstpy
Requires:	python-twisted-core python-twisted-names
# needed for http-streamer
Requires:	python-twisted-web
Requires:	pygtk2.0 >= %pygtk
Requires:	pygtk2.0-libglade >= %pygtk
Requires:	python-imaging
Requires:	fonts-ttf-bitstream-vera
Requires:	python-rrdtool
Requires:	python-kiwi
Requires(pre):  rpm-helper
Requires(post):	openssl
BuildRequires:	python-twisted-core python-twisted-names
BuildRequires:	python-twisted-web
BuildRequires:	gstreamer0.10-python-devel >= %gstpy
BuildRequires:	gstreamer0.10-devel >= 0.8.5
BuildRequires:	python >= 2.3
BuildRequires:	pygtk2.0-devel >= %pygtk
BuildRequires:	pygtk2.0-libglade >= %pygtk
BuildRequires:	python-rrdtool
BuildRequires:	python-kiwi
BuildRequires:	epydoc
BuildRequires:	imagemagick
BuildRequires:	desktop-file-utils

%description
Flumotion is a free Streaming Server developed by Fluendo Inc.
Available under a dual license, it allows you to stream content using free
codecs, such as Ogg/Vorbis and Ogg/Theora, from a wide range of device, 
like FireWire cameras, ALSA and OSS sound card or TV capture cards

Modular by design, it can also distribute the load on several networked 
computers, and currently focus on live streaming.

Flumotion is written in Python on top of GStreamer and Twisted. 

%package doc 
Summary:    Flumotion server reference documentation
Group:      System/Servers

%description  doc
This package contains the reference documentation
of the Flumotion Streaming Server.

%prep
%setup -q
%patch -p1 -b .init

%build
./configure --prefix=%_prefix --libdir=%_libdir --sysconfdir=%_sysconfdir --localstatedir=%_var --mandir=%_mandir
%make

%install
rm -rf $RPM_BUILD_ROOT

%makeinstall_std
bzcat %SOURCE1 > %buildroot%_datadir/%name/make-dummy-cert
chmod 755 %buildroot%_datadir/%name/make-dummy-cert
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/flumotion/managers/default/flows
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/flumotion/workers

# install service files
install -d $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d
install -m 755 \
	doc/redhat/%name \
	$RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d

# create a .flumotion in the new home
# FIXME: needs to be done more gracefully

install -d -m 755 $RPM_BUILD_ROOT%{_var}/lib/flumotion/.flumotion

# create log directory
install -d $RPM_BUILD_ROOT%_var/log/flumotion
install -d $RPM_BUILD_ROOT%{_var}/run/flumotion
install -d $RPM_BUILD_ROOT%{_var}/cache/flumotion

mkdir -p %buildroot%_sysconfdir/logrotate.d/
cat > %buildroot%_sysconfdir/logrotate.d/%name << EOF
%_var/log/flumotion/*.log {
    notifempty
    missingok
    monthly
    compress
    postrotate
    	/bin/kill -HUP \$(cat /var/run/flumotion/*.pid 2> /dev/null) 2> /dev/null || true
    endscript
}
EOF

mkdir -p %buildroot%_sysconfdir/sysconfig/
cat > %buildroot%_sysconfdir/sysconfig/%name << EOF
# If you wish to add components to flumotion, use the following
# variable to point to the directory containing the component.
# Multiple paths can be given, provided they are separated with :
#FLU_REGISTRY_PATH=path1:path2

# Control the logging of the server.
# Must be a list of category and level, separated by a comma.
#  level : 1 to 5 ( ERROR, WARN, INFO, DEBUG, LOG )
#  category : see the source code 
#FLU_DEBUG="*:2,admin:4"
EOF

# menu
desktop-file-install --vendor="" \
  --remove-category="Application" \
  --add-category="X-MandrivaLinux-System-Configuration-Other" \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications $RPM_BUILD_ROOT%{_datadir}/applications/*


mkdir -p %buildroot{%_liconsdir,%_iconsdir,%_miconsdir}
ln -s %_datadir/pixmaps/%name.png %buildroot%_liconsdir/%name.png
convert -scale 32 data/image/%name.png %buildroot%_iconsdir/%name.png
convert -scale 16 data/image/%name.png %buildroot%_miconsdir/%name.png

rm -f %buildroot%_libdir/flumotion/python/flumotion/extern/pytrayicon/pytrayicon.la

#replace by symlink
ln -sf %_datadir/fonts/TTF/Vera.ttf %buildroot%_libdir/flumotion/python/flumotion/component/converters/overlay/

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%_pre_useradd flumotion %{_var}/lib/flumotion /sbin/nologin
/usr/sbin/usermod -G audio,video -d %{_var}/lib/flumotion flumotion

%post
%if %mdkversion < 200900
%update_menus
%endif
%_post_service flumotion
# generate a default .pem certificate ?
PEM_FILE="%{_sysconfdir}/flumotion/default.pem"
if ! test -e ${PEM_FILE}
then
  sh %{_datadir}/%name/make-dummy-cert ${PEM_FILE}
  chown :flumotion ${PEM_FILE}
  chmod 640 ${PEM_FILE}
fi

# create a default planet config if no manager configs present
# the default login will be user/test
# FIXME: still need a way of specifying we really do not want a default manager
if ! ls %{_sysconfdir}/flumotion/managers/*/*.xml >/dev/null 2>&1
then
  cat > %{_sysconfdir}/flumotion/managers/default/planet.xml <<EOF
<planet>
 
  <manager>
    <host>localhost</host>
<!--
    <port>7531</port>
    <transport>ssl</transport>
    <certificate>default.pem</certificate>
-->
    <component name="manager-bouncer" type="htpasswdcrypt">
      <property name="data"><![CDATA[
user:PSfNpHTkpTx1M
]]></property>
    </component>
  </manager>
 
</planet>
EOF
fi

# create a default worker config if no worker configs present
# the default login will be user/test
# FIXME: still need a way of specifying we really do not want a default worker
if ! test -e %{_sysconfdir}/flumotion/*/default.xml
then
  cat > %{_sysconfdir}/flumotion/workers/default.xml <<EOF
<worker>
 
  <!-- <debug>3</debug> -->

  <manager>
<!--
    <host>localhost</host>
    <port>7531</port>
-->
  </manager>

  <authentication type="plaintext">
    <username>user</username>
    <password>test</password>
  </authentication>
 
  <!-- <feederports>8600-8639</feederports> -->

</worker>
EOF

fi

%preun
%_preun_service flumotion

%postun
%if %mdkversion < 200900
%clean_menus
%endif
%_postun_userdel flumotion
# if removal and not upgrade, clean up user and config
if [ $1 -eq 0 ]
then
  /usr/sbin/userdel flumotion

  rm -rf %{_sysconfdir}/flumotion/*
  rm -rf %{_var}/lock/flumotion*
  rm -rf %{_var}/run/flumotion*
fi

%files doc
%doc doc/reference/html

%files
%defattr(-,root,root,-)
%doc ChangeLog COPYING README AUTHORS
%doc conf
%config(noreplace) %{_sysconfdir}/rc.d/init.d/%name
%config(noreplace) %_sysconfdir/logrotate.d/%name
%config(noreplace) %{_sysconfdir}/sysconfig/%name
%{_bindir}/flumotion-manager
%{_bindir}/flumotion-worker
%{_bindir}/flumotion-admin
%{_bindir}/flumotion-tester
%{_bindir}/flumotion-admin-text
%{_bindir}/flumotion-inspect
%{_bindir}/flumotion-job
%{_bindir}/flumotion-launch
%{_bindir}/flumotion-command
%{_bindir}/flumotion-nagios
%{_bindir}/flumotion-rrdmon
%{_sbindir}/flumotion
%{_libdir}/flumotion
%{_datadir}/applications/flumotion-admin.desktop
%{_datadir}/hal/fdi/policy/20thirdparty/91-flumotion-device-policy.fdi
%{_datadir}/pixmaps/flumotion.png
#gw yes, we need them all at runtime
%_datadir/locale/*/LC_MESSAGES/flumotion.mo
%dir %{_datadir}/flumotion
%{_datadir}/flumotion/*xsl
%{_datadir}/flumotion/*.html
%{_datadir}/flumotion/glade/
%{_datadir}/flumotion/image
%{_datadir}/flumotion/make-dummy-cert
%{_libdir}/pkgconfig/%name.pc
%attr(750,flumotion,root) %{_sysconfdir}/flumotion
%attr(750,flumotion,root) %{_var}/run/flumotion
%attr(750,flumotion,root) %{_var}/log/flumotion
%attr(750,flumotion,root) %{_var}/cache/flumotion
%attr(750,flumotion,root) %{_var}/lib/flumotion/
%_liconsdir/%name.png
%_iconsdir/%name.png
%_miconsdir/%name.png
%_mandir/man1/*


