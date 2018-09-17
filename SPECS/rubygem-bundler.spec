%global gem_name bundler

# Enable test when building on local.
%bcond_with tests

# Ideally it should be checked against FileUtils::VERSION.
# https://github.com/ruby/fileutils/pull/12
%global fileutils_version 0.7.2
%global molinillo_version 0.6.6
%global net_http_persistent_version 2.9.4
%global thor_version 0.20.0

Name: rubygem-%{gem_name}
Version: %{rpmbuild_version}
Release: %{rpmbuild_release}%{?dist}
Summary: Library and utilities to manage Ruby application gem dependencies
Group: Development/Languages
License: MIT
URL: https://bundler.io
Source0: https://rubygems.org/gems/%{gem_name}-%{version}.gem
%if %{with tests}
%undefine _disable_source_fetch
# git clone https://github.com/bundler/bundler.git && cd bundler
# git checkout v%{version} && tar czvf bundler-%{version}-specs.tar.gz spec/
Source1: https://s3.amazonaws.com/rome-repo/support-files/%{gem_name}-%{version}-specs.tar.gz
%endif
# ruby package has just soft dependency on rubygem(io-console), while
# Bundler always requires it.
Requires: rubygem(io-console)
BuildRequires: ruby(release)
BuildRequires: rubygems-devel
BuildRequires: ruby
%if %{with tests}
BuildRequires: ruby-devel
BuildRequires: git
BuildRequires: %{_bindir}/ps
%endif
# https://github.com/bundler/bundler/issues/3647
Provides: bundled(rubygem-fileutils) = %{fileutils_version}
Provides: bundled(rubygem-molinillo) = %{molinillo_version}
Provides: bundled(rubygem-net-http-persisntent) = %{net_http_persistent_version}
Provides: bundled(rubygem-thor) = %{thor_version}
BuildArch: noarch

%description
Bundler manages Ruby application dependencies through its entire life, across
many machines, systematically and repeatably.


%package doc
Summary: Documentation for %{name}
Group: Documentation
Requires: %{name} = %{version}-%{release}
BuildArch: noarch

%description doc
Documentation for %{name}.

%prep
%setup -q -c -T
%gem_install -n %{SOURCE0}

%build

%install
mkdir -p %{buildroot}%{gem_dir}
cp -a .%{gem_dir}/* \
        %{buildroot}%{gem_dir}/


mkdir -p %{buildroot}%{_bindir}
cp -a .%{_bindir}/* \
        %{buildroot}%{_bindir}/

find %{buildroot}%{gem_instdir}/exe -type f | xargs chmod a+x

# Remove unnecessary executable bit.
# https://github.com/bundler/bundler/pull/6285
chmod a-x %{buildroot}%{gem_libdir}/bundler/templates/Executable

# Man pages are used by Bundler internally, do not remove them!
for n in 5 1; do
  mkdir -p %{buildroot}%{_mandir}/man${n}
  for file in %{buildroot}%{gem_instdir}/man/*.${n}; do
    base_name=$(basename "${file}")
    cp -a "${file}" "%{buildroot}%{_mandir}/man${n}/${base_name}"
  done
done

%check
pushd .%{gem_instdir}
# Check bundled libraries.
[ `ls lib/bundler/vendor | wc -l` == 4 ]

ruby -e '
  module Bundler; end
  require "./lib/bundler/vendor/fileutils/lib/fileutils.rb"'

[ `ruby -e '
  module Bundler; end
  require "./lib/bundler/vendor/molinillo/lib/molinillo/gem_metadata"
  puts Bundler::Molinillo::VERSION'` == '%{molinillo_version}' ]

[ `ruby -Ilib -e '
  module Bundler; module Persistent; module Net; module HTTP; end; end; end; end
  require "./lib/bundler/vendor/net-http-persistent/lib/net/http/persistent"
  puts Bundler::Persistent::Net::HTTP::Persistent::VERSION'` == '%{net_http_persistent_version}' ]

[ `ruby -e '
  module Bundler; end
  require "./lib/bundler/vendor/thor/lib/thor/version"
  puts Bundler::Thor::VERSION'` == '%{thor_version}' ]

# Test suite has to be disabled for official build, since it downloads various
# gems, which are not in Fedora or they have different version etc.
# Nevertheless, the test suite should run for local builds.
%if %{with tests}

tar xzvf %{SOURCE1}

# Re-create bundler.gemspec used in spec/spec_helper.rb to avoid unnecessary
# git dependency.
gem spec %{SOURCE0} -l --ruby > %{gem_name}.gemspec

# Color tests do not work in mock building process (but this can be tested
# running from shell).
# https://github.com/rpm-software-management/mock/issues/136
sed -i '/^          context "with color" do$/,/^          end$/ s/^/#/' \
  spec/bundler/source_spec.rb

# This test fails due to rubypick.
sed -i '/^      it "like a normally executed executable" do$/,/^      end$/ s/^/#/' \
  spec/commands/exec_spec.rb

# RDoc is not default gem on Fedora.
sed -i '/^    context "given a default gem shippped in ruby" do$/,/^    end$/ s/^/#/' \
  spec/commands/info_spec.rb

# Avoid unexpected influence of Fedora specific configuration. This forces
# Ruby to load this empty operating_system.rb instead of operatin_system.rb
# shipped as part of RubyGems.
mkdir -p %{_builddir}/rubygems/rubygems/defaults/
touch %{_builddir}/rubygems/rubygems/defaults/operating_system.rb

# It is necessary to require spec_helper.rb explicitly.
# https://github.com/bundler/bundler/pull/5634
RUBYOPT=-I%{_builddir}/rubygems GEM_PATH=%{gem_dir} rspec -rspec_helper spec -f d

%endif

popd

%files
%dir %{gem_instdir}
%{_bindir}/bundle
%{_bindir}/bundler
%exclude %{gem_instdir}/.*
%exclude %{gem_libdir}/bundler/ssl_certs/index.rubygems.org
%exclude %{gem_libdir}/bundler/ssl_certs/rubygems.global.ssl.fastly.net
%exclude %{gem_libdir}/bundler/ssl_certs/rubygems.org
%exclude %{gem_libdir}/bundler/ssl_certs/.document
%license %{gem_instdir}/LICENSE.md
%exclude %{gem_instdir}/bundler.gemspec
%{gem_instdir}/exe
%{gem_libdir}
%exclude %{gem_instdir}/man/*.ronn
%doc %{gem_instdir}/man
%exclude %{gem_cache}
%{gem_spec}
%doc %{_mandir}/man1/*
%doc %{_mandir}/man5/*

%files doc
%doc %{gem_docdir}
%doc %{gem_instdir}/CHANGELOG.md
%doc %{gem_instdir}/README.md

%changelog
* Mon Sep 17 2018 Justin Bronn <justin.bronn@radiantsolutions.com> - 1.16.4-1
- Initial release, Bundler 1.16.4
