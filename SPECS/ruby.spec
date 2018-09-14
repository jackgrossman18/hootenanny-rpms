%global major_version %(echo %{rpmbuild_version} | awk -F. '{ print $1 }')
%global minor_version %(echo %{rpmbuild_version} | awk -F. '{ print $2 }')
%global teeny_version %(echo %{rpmbuild_version} | awk -F. '{ print $3 }')
%global major_minor_version %{major_version}.%{minor_version}

%global ruby_version %{major_minor_version}.%{teeny_version}
%global ruby_release %{ruby_version}

# Keep the revision enabled for pre-releases from SVN.
#%%global revision 63024

%global ruby_archive %{name}-%{ruby_version}

# If revision and milestone are removed/commented out, the official release build is expected.
%if 0%{?milestone:1}%{?revision:1} != 0
%global development_release %{?milestone}%{?!milestone:%{?revision:r%{revision}}}
%global ruby_archive %{ruby_archive}-%{?milestone}%{?!milestone:%{?revision:r%{revision}}}
%endif

%global release %{rpmbuild_release}
%{!?release_string:%global release_string %{?development_release:0.}%{release}%{?development_release:.%{development_release}}%{?dist}}

# The RubyGems library has to stay out of Ruby directory three, since the
# RubyGems should be share by all Ruby implementations.
%global rubygems_dir %{_datadir}/rubygems

# Bundled libraries versions
%global rubygems_version 2.5.2.3
%global molinillo_version 0.4.1

# TODO: The IRB has strange versioning. Keep the Ruby's versioning ATM.
# http://redmine.ruby-lang.org/issues/5313
%global irb_version %{ruby_version}

%global bigdecimal_version 1.2.8
%global did_you_mean_version 1.0.0
%global io_console_version 0.4.5
%global json_version 1.8.3.1
%global minitest_version 5.8.5
%global power_assert_version 0.2.6
%global psych_version 2.1.0.1
%global rake_version 10.4.2
%global rdoc_version 4.2.1
%global net_telnet_version 0.1.1
%global test_unit_version 3.1.5

# Might not be needed in the future, if we are lucky enough.
# https://bugzilla.redhat.com/show_bug.cgi?id=888262
%global tapset_root %{_datadir}/systemtap
%global tapset_dir %{tapset_root}/tapset
%global tapset_libdir %(echo %{_libdir} | sed 's/64//')*

%global _normalized_cpu %(echo %{_target_cpu} | sed 's/^ppc/powerpc/;s/i.86/i386/;s/sparcv./sparc/')

Summary: An interpreter of object-oriented scripting language
Name: ruby
Version: %{ruby_version}
Release: %{release_string}
Group: Development/Languages
# Public Domain for example for: include/ruby/st.h, strftime.c, missing/*, ...
# MIT and CCO: ccan/*
# zlib: ext/digest/md5/md5.*, ext/nkf/nkf-utf8/nkf.c
# UCD: some of enc/trans/**/*.src
License: (Ruby or BSD) and Public Domain and MIT and CC0 and zlib and UCD
URL: http://ruby-lang.org/
Source0: https://cache.ruby-lang.org/pub/%{name}/%{major_minor_version}/%{ruby_archive}.tar.xz
Source1: operating_system.rb
# TODO: Try to push SystemTap support upstream.
Source2: libruby.stp
Source3: ruby-exercise.stp
Source4: macros.ruby
Source5: macros.rubygems
Source6: abrt_prelude.rb
# This wrapper fixes https://bugzilla.redhat.com/show_bug.cgi?id=977941
# Hopefully, it will get removed soon:
# https://fedorahosted.org/fpc/ticket/312
# https://bugzilla.redhat.com/show_bug.cgi?id=977941
Source7: config.h
# RPM dependency generators.
Source8: rubygems.attr
Source9: rubygems.req
Source10: rubygems.prov
# ABRT hoook test case.
Source12: test_abrt.rb
# SystemTap tests.
Source13: test_systemtap.rb

# Include the constants defined in macros files.
# http://rpm.org/ticket/866
%{lua:

function source_macros(file)
  local macro = nil

  for line in io.lines(file) do
    if not macro and line:match("^%%") then
      macro = line:match("^%%(.*)$")
      line = nil
    end

    if macro then
      if line and macro:match("^.-%s*\\%s*$") then
        macro = macro .. '\n' .. line
      end

      if not macro:match("^.-%s*\\%s*$") then
        rpm.define(macro)
        macro = nil
      end
    end
  end
end

source_macros(rpm.expand("%{SOURCE4}"))
source_macros(rpm.expand("%{SOURCE5}"))

}

# Fix ruby_version abuse.
# https://bugs.ruby-lang.org/issues/11002
Patch0: ruby-2.3.0-ruby_version.patch
# http://bugs.ruby-lang.org/issues/7807
Patch1: ruby-2.1.0-Prevent-duplicated-paths-when-empty-version-string-i.patch
# Allows to override libruby.so placement. Hopefully we will be able to return
# to plain --with-rubyarchprefix.
# http://bugs.ruby-lang.org/issues/8973
Patch2: ruby-2.1.0-Enable-configuration-of-archlibdir.patch
# Force multiarch directories for i.86 to be always named i386. This solves
# some differencies in build between Fedora and RHEL.
Patch3: ruby-2.1.0-always-use-i386.patch
# Allows to install RubyGems into custom directory, outside of Ruby's tree.
# http://bugs.ruby-lang.org/issues/5617
Patch4: ruby-2.1.0-custom-rubygems-location.patch
# Make mkmf verbose by default
Patch5: ruby-1.9.3-mkmf-verbose.patch
# Adds support for '--with-prelude' configuration option. This allows to built
# in support for ABRT.
# http://bugs.ruby-lang.org/issues/8566
Patch6: ruby-2.1.0-Allow-to-specify-additional-preludes-by-configuratio.patch
# Use miniruby to regenerate prelude.c.
# https://bugs.ruby-lang.org/issues/10554
Patch7: ruby-2.2.3-Generate-preludes-using-miniruby.patch
# Workaround "an invalid stdio handle" error on PPC, due to recently introduced
# hardening features of glibc (rhbz#1361037).
# https://bugs.ruby-lang.org/issues/12666
Patch9: ruby-2.3.1-Rely-on-ldd-to-detect-glibc.patch
# Revert experimental rounding that does not work on i686:
# https://bugs.ruby-lang.org/issues/13980
Patch10: ruby-2.3.5-Revert-experimental-rounding-on-i686.patch
# CVE-2017-17790 - Command injection in lib/resolv.rb:lazy_initialize() allows
# arbitrary code execution
# https://bugs.ruby-lang.org/issues/14205
Patch11: ruby-2.5.0-fix-command-injection.patch
# https://bugs.ruby-lang.org/issues/14655
Patch12: ruby-2.5.1-TestTimeTZ-test-failures-Kiritimati-and-Lisbon.patch
# Do not freeze strings in generated .gemspec. This causes regressions
# and FTBFS in Fedora packages. This is revert of:
# https://github.com/rubygems/rubygems/commit/8eda3272d28010c768a05620de776e5a8195c1ae
# https://lists.fedoraproject.org/archives/list/ruby-sig@lists.fedoraproject.org/message/NLZRTNIMG7NB5V3D4PAQKQLYEKC2TQSY/
Patch100: ruby-2.3.3-Revert-use-frozen-strings-in-serialized-specs.patch

Requires: %{name}-libs%{?_isa} = %{version}-%{release}
Requires: ruby(rubygems) >= %{rubygems_version}
Requires: rubygem(bigdecimal) >= %{bigdecimal_version}

BuildRequires: autoconf
BuildRequires: gdbm-devel
BuildRequires: libffi-devel
BuildRequires: openssl-devel
BuildRequires: libyaml-devel
BuildRequires: readline-devel
BuildRequires: tk-devel
# Needed to pass test_set_program_name(TestRubyOptions)
BuildRequires: procps
BuildRequires: %{_bindir}/dtrace
# RubyGems test suite optional dependencies.
BuildRequires: git
BuildRequires: %{_bindir}/cmake

Provides: ruby(runtime_executable) = %{ruby_release}

%description
Ruby is the interpreted scripting language for quick and easy
object-oriented programming.  It has many features to process text
files and to do system management tasks (as in Perl).  It is simple,
straight-forward, and extensible.


%package devel
Summary:    A Ruby development environment
Group:      Development/Languages
Requires:   %{name}%{?_isa} = %{version}-%{release}
Requires:   redhat-rpm-config
Requires:   rubygems

%description devel
Header files and libraries for building an extension library for the
Ruby or an application embedding Ruby.

%package libs
Summary:    Libraries necessary to run Ruby
Group:      Development/Libraries
License:    Ruby or BSD
Provides:   ruby(release) = %{ruby_release}

# Virtual provides for CCAN copylibs.
# https://fedorahosted.org/fpc/ticket/364
Provides: bundled(ccan-build_assert)
Provides: bundled(ccan-check_type)
Provides: bundled(ccan-container_of)
Provides: bundled(ccan-list)

%description libs
This package includes the libruby, necessary to run Ruby.


# TODO: Rename or not rename to ruby-rubygems?
%package -n rubygems
Summary:    The Ruby standard for packaging ruby libraries
Version:    %{rubygems_version}
Group:      Development/Libraries
License:    Ruby or MIT
Requires:   ruby(release)
Requires:   rubygem(rdoc) >= %{rdoc_version}
Requires:   rubygem(io-console) >= %{io_console_version}
Requires:   rubygem(psych) >= %{psych_version}
Requires:   ca-certificates
Provides:   gem = %{version}-%{release}
Provides:   ruby(rubygems) = %{version}-%{release}
# https://github.com/rubygems/rubygems/pull/1189#issuecomment-121600910
Provides:   bundled(rubygem-molinillo) = %{molinillo_version}
BuildArch:  noarch

%description -n rubygems
RubyGems is the Ruby standard for publishing and managing third party
libraries.


%package -n rubygems-devel
Summary:    Macros and development tools for packaging RubyGems
Version:    %{rubygems_version}
Group:      Development/Libraries
License:    Ruby or MIT
Requires:   ruby(rubygems) = %{version}-%{release}
# Needed for RDoc documentation format generation.
Requires:   rubygem(json) >= %{json_version}
Requires:   rubygem(rdoc) >= %{rdoc_version}
BuildArch:  noarch

%description -n rubygems-devel
Macros and development tools for packaging RubyGems.


%package -n rubygem-rake
Summary:    Ruby based make-like utility
Version:    %{rake_version}
Group:      Development/Libraries
License:    MIT
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rake = %{version}-%{release}
Provides:   rubygem(rake) = %{version}-%{release}
BuildArch:  noarch

%description -n rubygem-rake
Rake is a Make-like program implemented in Ruby. Tasks and dependencies are
specified in standard Ruby syntax.


%package irb
Summary:    The Interactive Ruby
Version:    %{irb_version}
Group:      Development/Libraries
Requires:   %{name}-libs = %{ruby_version}
Provides:   irb = %{version}-%{release}
Provides:   ruby(irb) = %{version}-%{release}
BuildArch:  noarch

%description irb
The irb is acronym for Interactive Ruby.  It evaluates ruby expression
from the terminal.


%package -n rubygem-rdoc
Summary:    A tool to generate HTML and command-line documentation for Ruby projects
Version:    %{rdoc_version}
Group:      Development/Libraries
# SIL: lib/rdoc/generator/template/darkfish/css/fonts.css
License:    GPLv2 and Ruby and MIT and OFL
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Requires:   ruby(irb) = %{irb_version}
# Hardcode the dependency to keep it compatible with dependencies of the
# official rubygem-rdoc gem.
Requires:   rubygem(json) >= %{json_version}
Provides:   rdoc = %{version}-%{release}
Provides:   ri = %{version}-%{release}
Provides:   rubygem(rdoc) = %{version}-%{release}
BuildArch:  noarch

%description -n rubygem-rdoc
RDoc produces HTML and command-line documentation for Ruby projects.  RDoc
includes the 'rdoc' and 'ri' tools for generating and displaying online
documentation.


%package doc
Summary:    Documentation for %{name}
Group:      Documentation
Requires:   %{_bindir}/ri
BuildArch:  noarch

%description doc
This package contains documentation for %{name}.


%package -n rubygem-bigdecimal
Summary:    BigDecimal provides arbitrary-precision floating point decimal arithmetic
Version:    %{bigdecimal_version}
Group:      Development/Libraries
License:    Ruby or BSD
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(bigdecimal) = %{version}-%{release}

%description -n rubygem-bigdecimal
Ruby provides built-in support for arbitrary precision integer arithmetic.
For example:

42**13 -> 1265437718438866624512

BigDecimal provides similar support for very large or very accurate floating
point numbers. Decimal arithmetic is also useful for general calculation,
because it provides the correct answers people expect–whereas normal binary
floating point arithmetic often introduces subtle errors because of the
conversion between base 10 and base 2.


%package -n rubygem-did_you_mean
Summary:    "Did you mean?" experience in Ruby
Version:    %{did_you_mean_version}
Group:      Development/Libraries
License:    MIT
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(did_you_mean) = %{version}-%{release}
BuildArch:  noarch

%description -n rubygem-did_you_mean
"did you mean?" experience in Ruby: the error message will tell you the right
one when you misspelled something.


%package -n rubygem-io-console
Summary:    IO/Console is a simple console utilizing library
Version:    %{io_console_version}
Group:      Development/Libraries
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(io-console) = %{version}-%{release}

%description -n rubygem-io-console
IO/Console provides very simple and portable access to console. It does not
provide higher layer features, such like curses and readline.


%package -n rubygem-json
Summary:    This is a JSON implementation as a Ruby extension in C
Version:    %{json_version}
Group:      Development/Libraries
# UCD: ext/json/generator/generator.c
License:    (Ruby or GPLv2) and UCD
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(json) = %{version}-%{release}

%description -n rubygem-json
This is a implementation of the JSON specification according to RFC 4627.
You can think of it as a low fat alternative to XML, if you want to store
data to disk or transmit it over a network rather than use a verbose
markup language.


%package -n rubygem-minitest
Summary:    Minitest provides a complete suite of testing facilities
Version:    %{minitest_version}
Group:      Development/Libraries
License:    MIT
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(minitest) = %{version}-%{release}
BuildArch:  noarch

%description -n rubygem-minitest
minitest/unit is a small and incredibly fast unit testing framework.

minitest/spec is a functionally complete spec engine.

minitest/benchmark is an awesome way to assert the performance of your
algorithms in a repeatable manner.

minitest/mock by Steven Baker, is a beautifully tiny mock object
framework.

minitest/pride shows pride in testing and adds coloring to your test
output.


%package -n rubygem-power_assert
Summary:    Power Assert for Ruby
Version:    %{power_assert_version}
Group:      Development/Libraries
License:    Ruby or BSD
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(power_assert) = %{version}-%{release}
BuildArch:  noarch

%description -n rubygem-power_assert
Power Assert shows each value of variables and method calls in the expression.
It is useful for testing, providing which value wasn not correct when the
condition is not satisfied.


%package -n rubygem-psych
Summary:    A libyaml wrapper for Ruby
Version:    %{psych_version}
Group:      Development/Libraries
License:    MIT
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(psych) = %{version}-%{release}

%description -n rubygem-psych
Psych is a YAML parser and emitter. Psych leverages
libyaml[http://pyyaml.org/wiki/LibYAML] for its YAML parsing and emitting
capabilities. In addition to wrapping libyaml, Psych also knows how to
serialize and de-serialize most Ruby objects to and from the YAML format.


%package -n rubygem-net-telnet
Summary:    Provides telnet client functionality
Version:    %{net_telnet_version}
Group:      Development/Libraries
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Provides:   rubygem(net-telnet) = %{version}-%{release}
BuildArch:  noarch

%description -n rubygem-net-telnet
Provides telnet client functionality.

This class also has, through delegation, all the methods of a socket object
(by default, a TCPSocket, but can be set by the Proxy option to new()). This
provides methods such as close() to end the session and sysread() to read data
directly from the host, instead of via the waitfor() mechanism. Note that if
you do use sysread() directly when in telnet mode, you should probably pass
the output through preprocess() to extract telnet command sequences.


# The Summary/Description fields are rather poor.
# https://github.com/test-unit/test-unit/issues/73
%package -n rubygem-test-unit
Summary:    An xUnit family unit testing framework for Ruby
Version:    %{test_unit_version}
Group:      Development/Libraries
# lib/test/unit/diff.rb is a double license of the Ruby license and PSF license.
# lib/test-unit.rb is a dual license of the Ruby license and LGPLv2.1 or later.
License:    (Ruby or BSD) and (Ruby or BSD or Python) and (Ruby or BSD or LGPLv2+)
Requires:   ruby(release)
Requires:   ruby(rubygems) >= %{rubygems_version}
Requires:   rubygem(power_assert)
Provides:   rubygem(test-unit) = %{version}-%{release}
BuildArch:  noarch

%description -n rubygem-test-unit
Test::Unit (test-unit) is unit testing framework for Ruby, based on xUnit
principles. These were originally designed by Kent Beck, creator of extreme
programming software development methodology, for Smalltalk's SUnit. It allows
writing tests, checking results and automated testing in Ruby.

%package tcltk
Summary:    Tcl/Tk interface for scripting language Ruby
Group:      Development/Languages
Requires:   %{name}-libs%{?_isa} = %{ruby_version}
Provides:   ruby(tcltk) = %{ruby_version}-%{release}

%description tcltk
Tcl/Tk interface for the object-oriented scripting language Ruby.

%prep
%setup -q -n %{ruby_archive}

# Remove bundled libraries to be sure they are not used.
rm -rf ext/psych/yaml
rm -rf ext/fiddle/libffi*

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch9 -p1
%patch10 -p1
%patch11 -p1
%patch12 -p1
%patch100 -p1

# Provide an example of usage of the tapset:
cp -a %{SOURCE3} .

# Make abrt_prelude.rb available for compilation process. The prelude must be
# available together with Ruby's source due to
# https://github.com/ruby/ruby/blob/trunk/tool/compile_prelude.rb#L26
cp -a %{SOURCE6} .

%build
autoconf

%configure \
        --with-rubylibprefix='%{ruby_libdir}' \
        --with-archlibdir='%{_libdir}' \
        --with-rubyarchprefix='%{ruby_libarchdir}' \
        --with-sitedir='%{ruby_sitelibdir}' \
        --with-sitearchdir='%{ruby_sitearchdir}' \
        --with-vendordir='%{ruby_vendorlibdir}' \
        --with-vendorarchdir='%{ruby_vendorarchdir}' \
        --with-rubyhdrdir='%{_includedir}' \
        --with-rubyarchhdrdir='%{_includedir}' \
        --with-sitearchhdrdir='$(sitehdrdir)/$(arch)' \
        --with-vendorarchhdrdir='$(vendorhdrdir)/$(arch)' \
        --with-rubygemsdir='%{rubygems_dir}' \
        --with-ruby-pc='%{name}.pc' \
        --disable-rpath \
        --enable-shared \
        --with-ruby-version='' \
        --enable-multiarch \
        --with-prelude=./abrt_prelude.rb \

# Q= makes the build output more verbose and allows to check Fedora
# compiler options.
make %{?_smp_mflags} COPY="cp -p" Q=

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}

# Rename ruby/config.h to ruby/config-<arch>.h to avoid file conflicts on
# multilib systems and install config.h wrapper
mv %{buildroot}%{_includedir}/%{name}/config.h %{buildroot}%{_includedir}/%{name}/config-%{_arch}.h
install -m644 %{SOURCE7} %{buildroot}%{_includedir}/%{name}/config.h

# Version is empty if --with-ruby-version is specified.
# http://bugs.ruby-lang.org/issues/7807
sed -i 's/Version: \${ruby_version}/Version: %{ruby_version}/' %{buildroot}%{_libdir}/pkgconfig/%{name}.pc

# Kill bundled certificates, as they should be part of ca-certificates.
for cert in \
  Class3PublicPrimaryCertificationAuthority.pem \
  DigiCertHighAssuranceEVRootCA.pem \
  EntrustnetSecureServerCertificationAuthority.pem \
  GeoTrustGlobalCA.pem \
  AddTrustExternalCARoot.pem \
  AddTrustExternalCARoot-2048.pem \
  GlobalSignRootCA.pem
do
  rm %{buildroot}%{rubygems_dir}/rubygems/ssl_certs/$cert
done
# Ensure there is not forgotten any certificate.
test ! "$(ls -A  %{buildroot}%{rubygems_dir}/rubygems/ssl_certs/ 2>/dev/null)"

# Move macros file into proper place and replace the %%{name} macro, since it
# would be wrongly evaluated during build of other packages.
mkdir -p %{buildroot}%{_rpmconfigdir}/macros.d
install -m 644 %{SOURCE4} %{buildroot}%{_rpmconfigdir}/macros.d/macros.ruby
sed -i "s/%%{name}/%{name}/" %{buildroot}%{_rpmconfigdir}/macros.d/macros.ruby
install -m 644 %{SOURCE5} %{buildroot}%{_rpmconfigdir}/macros.d/macros.rubygems
sed -i "s/%%{name}/%{name}/" %{buildroot}%{_rpmconfigdir}/macros.d/macros.rubygems

# Install dependency generators.
mkdir -p %{buildroot}%{_rpmconfigdir}/fileattrs
install -m 644 %{SOURCE8} %{buildroot}%{_rpmconfigdir}/fileattrs
install -m 755 %{SOURCE9} %{buildroot}%{_rpmconfigdir}
install -m 755 %{SOURCE10} %{buildroot}%{_rpmconfigdir}

# Install custom operating_system.rb.
mkdir -p %{buildroot}%{rubygems_dir}/rubygems/defaults
cp %{SOURCE1} %{buildroot}%{rubygems_dir}/rubygems/defaults

# Move gems root into common direcotry, out of Ruby directory structure.
mv %{buildroot}%{ruby_libdir}/gems %{buildroot}%{gem_dir}

# Create folders for gem binary extensions.
# TODO: These folders should go into rubygem-filesystem but how to achieve it,
# since noarch package cannot provide arch dependent subpackages?
# http://rpm.org/ticket/78
mkdir -p %{buildroot}%{_exec_prefix}/lib{,64}/gems/%{name}

# Move bundled rubygems to %%gem_dir and %%gem_extdir_mri
# make symlinks for io-console and bigdecimal, which are considered to be part of stdlib by other Gems
mkdir -p %{buildroot}%{gem_dir}/gems/rdoc-%{rdoc_version}/lib
mv %{buildroot}%{ruby_libdir}/rdoc* %{buildroot}%{gem_dir}/gems/rdoc-%{rdoc_version}/lib
mv %{buildroot}%{gem_dir}/specifications/default/rdoc-%{rdoc_version}.gemspec %{buildroot}%{gem_dir}/specifications

mkdir -p %{buildroot}%{gem_dir}/gems/bigdecimal-%{bigdecimal_version}/lib
mkdir -p %{buildroot}%{_libdir}/gems/%{name}/bigdecimal-%{bigdecimal_version}
mv %{buildroot}%{ruby_libdir}/bigdecimal %{buildroot}%{gem_dir}/gems/bigdecimal-%{bigdecimal_version}/lib
mv %{buildroot}%{ruby_libarchdir}/bigdecimal.so %{buildroot}%{_libdir}/gems/%{name}/bigdecimal-%{bigdecimal_version}
mv %{buildroot}%{gem_dir}/specifications/default/bigdecimal-%{bigdecimal_version}.gemspec %{buildroot}%{gem_dir}/specifications
ln -s %{gem_dir}/gems/bigdecimal-%{bigdecimal_version}/lib/bigdecimal %{buildroot}%{ruby_libdir}/bigdecimal
ln -s %{_libdir}/gems/%{name}/bigdecimal-%{bigdecimal_version}/bigdecimal.so %{buildroot}%{ruby_libarchdir}/bigdecimal.so

mkdir -p %{buildroot}%{gem_dir}/gems/io-console-%{io_console_version}/lib
mkdir -p %{buildroot}%{_libdir}/gems/%{name}/io-console-%{io_console_version}/io
mv %{buildroot}%{ruby_libdir}/io %{buildroot}%{gem_dir}/gems/io-console-%{io_console_version}/lib
mv %{buildroot}%{ruby_libarchdir}/io/console.so %{buildroot}%{_libdir}/gems/%{name}/io-console-%{io_console_version}/io
mv %{buildroot}%{gem_dir}/specifications/default/io-console-%{io_console_version}.gemspec %{buildroot}%{gem_dir}/specifications
ln -s %{gem_dir}/gems/io-console-%{io_console_version}/lib/io %{buildroot}%{ruby_libdir}/io
ln -s %{_libdir}/gems/%{name}/io-console-%{io_console_version}/io/console.so %{buildroot}%{ruby_libarchdir}/io/console.so

mkdir -p %{buildroot}%{gem_dir}/gems/json-%{json_version}/lib
mkdir -p %{buildroot}%{_libdir}/gems/%{name}/json-%{json_version}
mv %{buildroot}%{ruby_libdir}/json* %{buildroot}%{gem_dir}/gems/json-%{json_version}/lib
mv %{buildroot}%{ruby_libarchdir}/json/ %{buildroot}%{_libdir}/gems/%{name}/json-%{json_version}/
mv %{buildroot}%{gem_dir}/specifications/default/json-%{json_version}.gemspec %{buildroot}%{gem_dir}/specifications
ln -s %{gem_dir}/gems/json-%{json_version}/lib/json.rb %{buildroot}%{ruby_libdir}/json.rb
ln -s %{gem_dir}/gems/json-%{json_version}/lib/json %{buildroot}%{ruby_libdir}/json
ln -s %{_libdir}/gems/%{name}/json-%{json_version}/json/ %{buildroot}%{ruby_libarchdir}/json

mkdir -p %{buildroot}%{gem_dir}/gems/psych-%{psych_version}/lib
mkdir -p %{buildroot}%{_libdir}/gems/%{name}/psych-%{psych_version}
mv %{buildroot}%{ruby_libdir}/psych* %{buildroot}%{gem_dir}/gems/psych-%{psych_version}/lib
mv %{buildroot}%{ruby_libarchdir}/psych.so %{buildroot}%{_libdir}/gems/%{name}/psych-%{psych_version}/
mv %{buildroot}%{gem_dir}/specifications/default/psych-%{psych_version}.gemspec %{buildroot}%{gem_dir}/specifications
ln -s %{gem_dir}/gems/psych-%{psych_version}/lib/psych %{buildroot}%{ruby_libdir}/psych
ln -s %{gem_dir}/gems/psych-%{psych_version}/lib/psych.rb %{buildroot}%{ruby_libdir}/psych.rb
ln -s %{_libdir}/gems/%{name}/psych-%{psych_version}/psych.so %{buildroot}%{ruby_libarchdir}/psych.so

# Adjust the gemspec files so that the gems will load properly
sed -i '/^end$/ i\
  s.extensions = ["json/ext/parser.so", "json/ext/generator.so"]' %{buildroot}%{gem_dir}/specifications/json-%{json_version}.gemspec

# Move man pages into proper location
mv %{buildroot}%{gem_dir}/gems/rake-%{rake_version}/doc/rake.1 %{buildroot}%{_mandir}/man1

# Install a tapset and fix up the path to the library.
mkdir -p %{buildroot}%{tapset_dir}
sed -e "s|@LIBRARY_PATH@|%{tapset_libdir}/libruby.so.%{major_minor_version}|" \
  %{SOURCE2} > %{buildroot}%{tapset_dir}/libruby.so.%{major_minor_version}.stp
# Escape '*/' in comment.
sed -i -r "s|( \*.*\*)\/(.*)|\1\\\/\2|" %{buildroot}%{tapset_dir}/libruby.so.%{major_minor_version}.stp

# Prepare -doc subpackage file lists.
find doc -maxdepth 1 -type f ! -name '.*' ! -name '*.ja*' > .ruby-doc.en
echo 'doc/images' >> .ruby-doc.en
echo 'doc/syntax' >> .ruby-doc.en

find doc -maxdepth 1 -type f -name '*.ja*' > .ruby-doc.ja
echo 'doc/irb' >> .ruby-doc.ja
echo 'doc/pty' >> .ruby-doc.ja

sed -i 's/^/%doc /' .ruby-doc.*
sed -i 's/^/%lang(ja) /' .ruby-doc.ja

%check
# Check RubyGems version correctness.
[ "`make runruby TESTRUN_SCRIPT='bin/gem -v' | tail -1`" == '%{rubygems_version}' ]
# Check Molinillo version correctness.
[ "`make runruby TESTRUN_SCRIPT=\"-e \\\"module Gem; module Resolver; end; end; require 'rubygems/resolver/molinillo/lib/molinillo/gem_metadata'; puts Gem::Resolver::Molinillo::VERSION\\\"\" | tail -1`" \
  == '%{molinillo_version}' ]

# test_debug(TestRubyOptions) fails due to LoadError reported in debug mode,
# when abrt.rb cannot be required (seems to be easier way then customizing
# the test suite).
touch abrt.rb

# Check if abrt hook is required (RubyGems are disabled by default when using
# runruby, so re-enable them).
make runruby TESTRUN_SCRIPT="--enable-gems %{SOURCE12}"

# Check if systemtap is supported.
make runruby TESTRUN_SCRIPT=%{SOURCE13}

DISABLE_TESTS=""

# https://bugs.ruby-lang.org/issues/11480
# Once seen: http://koji.fedoraproject.org/koji/taskinfo?taskID=12556650
DISABLE_TESTS="$DISABLE_TESTS -x test_fork.rb"

make check TESTS="-v $DISABLE_TESTS"

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%files
%doc BSDL
%doc COPYING
%lang(ja) %doc COPYING.ja
%doc GPL
%doc LEGAL
%{_bindir}/erb
%{_bindir}/%{name}
%{_mandir}/man1/erb*
%{_mandir}/man1/ruby*

# http://fedoraproject.org/wiki/Packaging:Guidelines#Packaging_Static_Libraries
%exclude %{_libdir}/libruby-static.a

%files devel
%doc BSDL
%doc COPYING
%lang(ja) %doc COPYING.ja
%doc GPL
%doc LEGAL

%{_rpmconfigdir}/macros.d/macros.ruby

%{_includedir}/*
%{_libdir}/libruby.so
%{_libdir}/pkgconfig/%{name}.pc

%files libs
%doc COPYING
%lang(ja) %doc COPYING.ja
%doc GPL
%doc LEGAL
%doc README.md
%doc NEWS
# Exclude /usr/local directory since it is supposed to be managed by
# local system administrator.
%exclude %{ruby_sitelibdir}
%exclude %{ruby_sitearchdir}
%dir %{ruby_vendorlibdir}
%dir %{ruby_vendorarchdir}

# List all these files explicitly to prevent surprises
# Platform independent libraries.
%dir %{ruby_libdir}
%{ruby_libdir}/*.rb
%exclude %{ruby_libdir}/*-tk.rb
%exclude %{ruby_libdir}/irb.rb
%exclude %{ruby_libdir}/json.rb
%exclude %{ruby_libdir}/tcltk.rb
%exclude %{ruby_libdir}/tk*.rb
%exclude %{ruby_libdir}/psych.rb
%{ruby_libdir}/cgi
%{ruby_libdir}/digest
%{ruby_libdir}/drb
%{ruby_libdir}/fiddle
%exclude %{ruby_libdir}/irb
%{ruby_libdir}/matrix
%{ruby_libdir}/net
%{ruby_libdir}/openssl
%{ruby_libdir}/optparse
%{ruby_libdir}/racc
%{ruby_libdir}/rbconfig
%{ruby_libdir}/rexml
%{ruby_libdir}/rinda
%{ruby_libdir}/ripper
%{ruby_libdir}/rss
%{ruby_libdir}/shell
%{ruby_libdir}/syslog
%exclude %{ruby_libdir}/tk
%exclude %{ruby_libdir}/tkextlib
%{ruby_libdir}/unicode_normalize
%{ruby_libdir}/uri
%{ruby_libdir}/webrick
%{ruby_libdir}/xmlrpc
%{ruby_libdir}/yaml

# Platform specific libraries.
%{_libdir}/libruby.so.*
%dir %{ruby_libarchdir}
%dir %{ruby_libarchdir}/cgi
%{ruby_libarchdir}/cgi/escape.so
%{ruby_libarchdir}/continuation.so
%{ruby_libarchdir}/coverage.so
%{ruby_libarchdir}/date_core.so
%{ruby_libarchdir}/dbm.so
%dir %{ruby_libarchdir}/digest
%{ruby_libarchdir}/digest.so
%{ruby_libarchdir}/digest/bubblebabble.so
%{ruby_libarchdir}/digest/md5.so
%{ruby_libarchdir}/digest/rmd160.so
%{ruby_libarchdir}/digest/sha1.so
%{ruby_libarchdir}/digest/sha2.so
%dir %{ruby_libarchdir}/enc
%{ruby_libarchdir}/enc/big5.so
%{ruby_libarchdir}/enc/cp949.so
%{ruby_libarchdir}/enc/emacs_mule.so
%{ruby_libarchdir}/enc/encdb.so
%{ruby_libarchdir}/enc/euc_jp.so
%{ruby_libarchdir}/enc/euc_kr.so
%{ruby_libarchdir}/enc/euc_tw.so
%{ruby_libarchdir}/enc/gb18030.so
%{ruby_libarchdir}/enc/gb2312.so
%{ruby_libarchdir}/enc/gbk.so
%{ruby_libarchdir}/enc/iso_8859_1.so
%{ruby_libarchdir}/enc/iso_8859_10.so
%{ruby_libarchdir}/enc/iso_8859_11.so
%{ruby_libarchdir}/enc/iso_8859_13.so
%{ruby_libarchdir}/enc/iso_8859_14.so
%{ruby_libarchdir}/enc/iso_8859_15.so
%{ruby_libarchdir}/enc/iso_8859_16.so
%{ruby_libarchdir}/enc/iso_8859_2.so
%{ruby_libarchdir}/enc/iso_8859_3.so
%{ruby_libarchdir}/enc/iso_8859_4.so
%{ruby_libarchdir}/enc/iso_8859_5.so
%{ruby_libarchdir}/enc/iso_8859_6.so
%{ruby_libarchdir}/enc/iso_8859_7.so
%{ruby_libarchdir}/enc/iso_8859_8.so
%{ruby_libarchdir}/enc/iso_8859_9.so
%{ruby_libarchdir}/enc/koi8_r.so
%{ruby_libarchdir}/enc/koi8_u.so
%{ruby_libarchdir}/enc/shift_jis.so
%dir %{ruby_libarchdir}/enc/trans
%{ruby_libarchdir}/enc/trans/big5.so
%{ruby_libarchdir}/enc/trans/chinese.so
%{ruby_libarchdir}/enc/trans/ebcdic.so
%{ruby_libarchdir}/enc/trans/emoji.so
%{ruby_libarchdir}/enc/trans/emoji_iso2022_kddi.so
%{ruby_libarchdir}/enc/trans/emoji_sjis_docomo.so
%{ruby_libarchdir}/enc/trans/emoji_sjis_kddi.so
%{ruby_libarchdir}/enc/trans/emoji_sjis_softbank.so
%{ruby_libarchdir}/enc/trans/escape.so
%{ruby_libarchdir}/enc/trans/gb18030.so
%{ruby_libarchdir}/enc/trans/gbk.so
%{ruby_libarchdir}/enc/trans/iso2022.so
%{ruby_libarchdir}/enc/trans/japanese.so
%{ruby_libarchdir}/enc/trans/japanese_euc.so
%{ruby_libarchdir}/enc/trans/japanese_sjis.so
%{ruby_libarchdir}/enc/trans/korean.so
%{ruby_libarchdir}/enc/trans/single_byte.so
%{ruby_libarchdir}/enc/trans/transdb.so
%{ruby_libarchdir}/enc/trans/utf8_mac.so
%{ruby_libarchdir}/enc/trans/utf_16_32.so
%{ruby_libarchdir}/enc/utf_16be.so
%{ruby_libarchdir}/enc/utf_16le.so
%{ruby_libarchdir}/enc/utf_32be.so
%{ruby_libarchdir}/enc/utf_32le.so
%{ruby_libarchdir}/enc/windows_1250.so
%{ruby_libarchdir}/enc/windows_1251.so
%{ruby_libarchdir}/enc/windows_1252.so
%{ruby_libarchdir}/enc/windows_31j.so
%{ruby_libarchdir}/etc.so
%{ruby_libarchdir}/fcntl.so
%{ruby_libarchdir}/fiber.so
%{ruby_libarchdir}/fiddle.so
%{ruby_libarchdir}/gdbm.so
%dir %{ruby_libarchdir}/io
%{ruby_libarchdir}/io/nonblock.so
%{ruby_libarchdir}/io/wait.so
%dir %{ruby_libarchdir}/mathn
%{ruby_libarchdir}/mathn/complex.so
%{ruby_libarchdir}/mathn/rational.so
%{ruby_libarchdir}/nkf.so
%{ruby_libarchdir}/objspace.so
%{ruby_libarchdir}/openssl.so
%{ruby_libarchdir}/pathname.so
%{ruby_libarchdir}/pty.so
%dir %{ruby_libarchdir}/racc
%{ruby_libarchdir}/racc/cparse.so
%dir %{ruby_libarchdir}/rbconfig
%{ruby_libarchdir}/rbconfig.rb
%{ruby_libarchdir}/rbconfig/sizeof.so
%{ruby_libarchdir}/readline.so
%{ruby_libarchdir}/ripper.so
%{ruby_libarchdir}/sdbm.so
%{ruby_libarchdir}/socket.so
%{ruby_libarchdir}/stringio.so
%{ruby_libarchdir}/strscan.so
%{ruby_libarchdir}/syslog.so
%exclude %{ruby_libarchdir}/tcltklib.so
%{ruby_libarchdir}/thread.so
%exclude %{ruby_libarchdir}/tkutil.so
%{ruby_libarchdir}/zlib.so

%{tapset_root}

%files -n rubygems
%{_bindir}/gem
%{rubygems_dir}

# Explicitly include only RubyGems directory strucure to avoid accidentally
# packaged content.
%dir %{gem_dir}
%dir %{gem_dir}/build_info
%dir %{gem_dir}/cache
%dir %{gem_dir}/doc
%dir %{gem_dir}/extensions
%dir %{gem_dir}/gems
%dir %{gem_dir}/specifications
%dir %{gem_dir}/specifications/default
%dir %{_exec_prefix}/lib*/gems
%dir %{_exec_prefix}/lib*/gems/ruby

%exclude %{gem_dir}/cache/*

%files -n rubygems-devel
%{_rpmconfigdir}/macros.d/macros.rubygems
%{_rpmconfigdir}/fileattrs/rubygems.attr
%{_rpmconfigdir}/rubygems.req
%{_rpmconfigdir}/rubygems.prov

%files -n rubygem-rake
%{_bindir}/rake
%{gem_dir}/gems/rake-%{rake_version}
%{gem_dir}/specifications/rake-%{rake_version}.gemspec
%{_mandir}/man1/rake.1*

%files irb
%{_bindir}/irb
%{ruby_libdir}/irb.rb
%{ruby_libdir}/irb
%{_mandir}/man1/irb.1*

%files -n rubygem-rdoc
%{_bindir}/rdoc
%{_bindir}/ri
%{gem_dir}/gems/rdoc-%{rdoc_version}
%{gem_dir}/specifications/rdoc-%{rdoc_version}.gemspec
%{_mandir}/man1/ri*

%files doc -f .ruby-doc.en -f .ruby-doc.ja
%doc README.md
%doc ChangeLog
%doc ruby-exercise.stp
%{_datadir}/ri

%files -n rubygem-bigdecimal
%{ruby_libdir}/bigdecimal
%{ruby_libarchdir}/bigdecimal.so
%{_libdir}/gems/%{name}/bigdecimal-%{bigdecimal_version}
%{gem_dir}/gems/bigdecimal-%{bigdecimal_version}
%{gem_dir}/specifications/bigdecimal-%{bigdecimal_version}.gemspec

%files -n rubygem-did_you_mean
%{gem_dir}/gems/did_you_mean-%{did_you_mean_version}
%exclude %{gem_dir}/gems/did_you_mean-%{did_you_mean_version}/.*
%{gem_dir}/specifications/did_you_mean-%{did_you_mean_version}.gemspec

%files -n rubygem-io-console
%{ruby_libdir}/io
%{ruby_libarchdir}/io/console.so
%{_libdir}/gems/%{name}/io-console-%{io_console_version}
%{gem_dir}/gems/io-console-%{io_console_version}
%{gem_dir}/specifications/io-console-%{io_console_version}.gemspec

%files -n rubygem-json
%{ruby_libdir}/json*
%{ruby_libarchdir}/json*
%{_libdir}/gems/%{name}/json-%{json_version}
%{gem_dir}/gems/json-%{json_version}
%{gem_dir}/specifications/json-%{json_version}.gemspec

%files -n rubygem-minitest
%{gem_dir}/gems/minitest-%{minitest_version}
%exclude %{gem_dir}/gems/minitest-%{minitest_version}/.*
%{gem_dir}/specifications/minitest-%{minitest_version}.gemspec

%files -n rubygem-power_assert
%{gem_dir}/gems/power_assert-%{power_assert_version}
%exclude %{gem_dir}/gems/power_assert-%{power_assert_version}/.*
%{gem_dir}/specifications/power_assert-%{power_assert_version}.gemspec

%files -n rubygem-psych
%{ruby_libdir}/psych
%{ruby_libdir}/psych.rb
%{ruby_libarchdir}/psych.so
%{_libdir}/gems/%{name}/psych-%{psych_version}
%{gem_dir}/gems/psych-%{psych_version}
%{gem_dir}/specifications/psych-%{psych_version}.gemspec

%files -n rubygem-net-telnet
%{gem_dir}/gems/net-telnet-%{net_telnet_version}
%exclude %{gem_dir}/gems/net-telnet-%{net_telnet_version}/.*
%{gem_dir}/specifications/net-telnet-%{net_telnet_version}.gemspec

%files -n rubygem-test-unit
%{gem_dir}/gems/test-unit-%{test_unit_version}
%{gem_dir}/specifications/test-unit-%{test_unit_version}.gemspec

%files tcltk
%{ruby_libdir}/*-tk.rb
%{ruby_libdir}/tcltk.rb
%{ruby_libdir}/tk*.rb
%{ruby_libarchdir}/tcltklib.so
%{ruby_libarchdir}/tkutil.so
%{ruby_libdir}/tk
%{ruby_libdir}/tkextlib

%changelog
* Thu Sep 13 2018 Justin Bronn <justin.bronn@radiantsolutions.com> - 2.3.7-1
- Initial release, Ruby 2.3.7.
