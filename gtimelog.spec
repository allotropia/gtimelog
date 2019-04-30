Name: 		gtimelog
Epoch:          1
Version: 	0.2.3
Release:	5%{?dist}
Summary: 	GTimeLog is a graphical (Gtk+) application for keeping track of time.

Group:		Office
License:	GPL
URL:		http://git.collabora.co.uk/?p=gtimelog.git;a=summary
Source0:	gtimelog-0.2.3.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	python python-setuptools
Requires:	python m2crypto

%define debug_package %{nil}

%description
GTimeLog is a graphical (Gtk+) application for keeping track of time.


%prep
%setup -q


%build
python2 setup.py build


%install
rm -rf %{buildroot}
python2 setup.py install --single-version-externally-managed --root=%{buildroot}
mkdir -p %{buildroot}/usr/share/pixmaps
cp src/gtimelog/gtimelog*.png %{buildroot}/usr/share/pixmaps
mkdir -p %{buildroot}/usr/share/applications
cp gtimelog.desktop %{buildroot}/usr/share/applications


%files
%defattr(-,root,root,-)
%doc
/usr/bin/rltimelog
/usr/bin/gtimelog
/usr/lib/python2.7/site-packages/gtimelog-0.2.3-py2.7.egg-info/PKG-INFO
/usr/lib/python2.7/site-packages/gtimelog-0.2.3-py2.7.egg-info/SOURCES.txt
/usr/lib/python2.7/site-packages/gtimelog-0.2.3-py2.7.egg-info/dependency_links.txt
/usr/lib/python2.7/site-packages/gtimelog-0.2.3-py2.7.egg-info/entry_points.txt
/usr/lib/python2.7/site-packages/gtimelog-0.2.3-py2.7.egg-info/not-zip-safe
/usr/lib/python2.7/site-packages/gtimelog-0.2.3-py2.7.egg-info/top_level.txt
/usr/lib/python2.7/site-packages/gtimelog/__init__.py
/usr/lib/python2.7/site-packages/gtimelog/__init__.pyc
/usr/lib/python2.7/site-packages/gtimelog/__init__.pyo
/usr/lib/python2.7/site-packages/gtimelog/gtimelog.png
/usr/lib/python2.7/site-packages/gtimelog/gtimelog.py
/usr/lib/python2.7/site-packages/gtimelog/gtimelog.pyc
/usr/lib/python2.7/site-packages/gtimelog/gtimelog.pyo
/usr/lib/python2.7/site-packages/gtimelog/rltimelog.py
/usr/lib/python2.7/site-packages/gtimelog/rltimelog.pyc
/usr/lib/python2.7/site-packages/gtimelog/rltimelog.pyo
/usr/lib/python2.7/site-packages/gtimelog/gtimelog.ui
/usr/lib/python2.7/site-packages/gtimelog/test_gtimelog.py
/usr/lib/python2.7/site-packages/gtimelog/test_gtimelog.pyc
/usr/lib/python2.7/site-packages/gtimelog/test_gtimelog.pyo
/usr/share/applications/gtimelog.desktop
/usr/share/pixmaps/gtimelog.png


%clean
rm -rf %{buildroot}

%changelog

