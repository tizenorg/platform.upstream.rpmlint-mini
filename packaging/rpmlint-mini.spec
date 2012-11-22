Name:           rpmlint-mini
BuildRequires:  glib2-devel
BuildRequires:  glib2-devel-static
BuildRequires:  pkg-config
BuildRequires:  python-magic
BuildRequires:  python-xml
BuildRequires:  python-rpm
BuildRequires:  rpmlint
# need to fetch the file from there
#BuildRequires:  checkbashisms
BuildRequires:  dash
BuildRequires:  libtool
BuildRequires:  polkit-default-privs
Requires:       cpio
Summary:        Rpm correctness checker
License:        GPL-2.0+
Group:          System/Packages
Version:        1.3
Release:        0
Url:            http://rpmlint.zarb.org/
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
Source:         desktop-file-utils-0.20.tar.xz
Source100:      rpmlint-deps.txt
Source101:      rpmlint.wrapper
Source102:      rpmlint-mini.config
Source103:      polkit-default-privs.config
Source1000:     rpmlint-mini.rpmlintrc

%description
Rpmlint is a tool to check common errors on rpm packages. Binary and
source packages can be checked.

%prep
%setup -q -n desktop-file-utils-0.20
[[ -r COPYING ]]

%build
%configure
pushd src
make desktop-file-validate V=1 DESKTOP_FILE_UTILS_LIBS="%{_libdir}/libglib-2.0.a -lpthread -lrt"
popd

%install
# test if the rpmlint works at all
set +e
/usr/bin/rpmlint rpmlint
test $? -gt 0 -a $? -lt 60 && exit 1
set -e
# okay, lets put it together
mkdir -p $RPM_BUILD_ROOT/opt/testing/share/rpmlint
install -m 755 -D src/desktop-file-validate $RPM_BUILD_ROOT/opt/testing/bin/desktop-file-validate
cp -a /bin/dash /usr/bin/checkbashisms $RPM_BUILD_ROOT/opt/testing/bin
cp -a /usr/share/rpmlint/*.py $RPM_BUILD_ROOT/opt/testing/share/rpmlint
# install config files
install -d -m 755 $RPM_BUILD_ROOT/opt/testing/share/rpmlint/mini
for i in /etc/rpmlint/{rpmgroups,pie,licenses}.config "%{SOURCE103}"; do
  cp $i $RPM_BUILD_ROOT/opt/testing/share/rpmlint/mini
done
install -m 644 -D /usr/share/rpmlint/config $RPM_BUILD_ROOT/opt/testing/share/rpmlint/config
install -m 644 "%{SOURCE102}" $RPM_BUILD_ROOT/opt/testing/share/rpmlint
# extra data
install -m 755 -d $RPM_BUILD_ROOT/opt/testing/share/rpmlint/data
install -m 644 /etc/polkit-default-privs.standard $RPM_BUILD_ROOT/opt/testing/share/rpmlint/data
install -m 644 -D /usr/include/python%{py_ver}/pyconfig.h $RPM_BUILD_ROOT/opt/testing/include/python%{py_ver}/pyconfig.h
#
cd %{py_libdir}
for f in $(<%{SOURCE100}); do
  find -path "*/$f" -exec install -D {} $RPM_BUILD_ROOT/opt/testing/%{_lib}/python%{py_ver}/{} \;
done
install -m 644 /usr/lib/python%{py_ver}/site-packages/magic.py $RPM_BUILD_ROOT/opt/testing/%{_lib}/python%{py_ver}/site-packages/magic.py
install -D /usr/bin/python $RPM_BUILD_ROOT/opt/testing/bin/python
cp -a %_libdir/libmagic.so.* $RPM_BUILD_ROOT/opt/testing/%{_lib}
cp -a %_libdir/libpython%{py_ver}.so.* $RPM_BUILD_ROOT/opt/testing/%{_lib}
cp -a %_bindir/rpmlint $RPM_BUILD_ROOT/opt/testing/share/rpmlint/rpmlint.py
pushd $RPM_BUILD_ROOT/opt/testing/share/rpmlint
PYTHONOPTIMIZE=1 python %py_libdir/py_compile.py *.py
rm *.py
popd
pushd $RPM_BUILD_ROOT/opt/testing/%{_lib}/python%{py_ver}/site-packages/
PYTHONOPTIMIZE=1 python %py_libdir/py_compile.py *.py
rm *.py
popd
rm -rf $RPM_BUILD_ROOT/{usr,etc}
rm -f $RPM_BUILD_ROOT/opt/testing/bin/rpmlint
install -m 755 -D %{SOURCE101} $RPM_BUILD_ROOT/opt/testing/bin/rpmlint
# hackatlon
%define my_requires %{_builddir}/%{?buildsubdir}/%{name}-requires
cat << EOF > %my_requires
cat - > file.list
%{__find_requires} < file.list > requires.list
%{__find_provides} < file.list > provides.list
while read i; do
    grep -F -v "\$i" requires.list > requires.list.new
    mv requires.list.new requires.list
done < provides.list
cat requires.list
rm -f requires.list provides.list file.list
EOF
chmod +x %my_requires
%define _use_internal_dependency_generator 0
%define __find_requires %my_requires
%define __find_provides %nil
# final run check to detect python dep changes
LD_LIBRARY_PATH=$RPM_BUILD_ROOT/opt/testing/%_lib
PYTHONPATH=$RPM_BUILD_ROOT/opt/testing/share/rpmlint
export PYTHONPATH LD_LIBRARY_PATH
$RPM_BUILD_ROOT/opt/testing/bin/python -tt -u -O $RPM_BUILD_ROOT/opt/testing/share/rpmlint/rpmlint.pyo --help || exit 1
echo ".. ok"

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,0755)
/opt/testing
%doc COPYING

%changelog
