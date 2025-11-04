Name:           wapiti_swagger
Version:        0.1.9
Release:        1%{?dist}
Summary:        Python library designed to parse Swagger (OpenAPI) specifications

License:        MIT
URL:            https://github.com/wapiti-scanner/wapiti_swagger
Source0:        wapiti_swagger-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel

Requires:       python3-yaml >= 6.0

%description
The Wapiti Swagger Parser is a Python library designed to parse Swagger (OpenAPI) specifications and extract the necessary information to generate valid HTTP requests. It focuses on providing a clean, programmatic interface for analyzing Swagger files and creating request templates without relying on external tools for OpenAPI processing.

%prep
%autosetup -n wapiti_swagger-%{version}

%build
%pyproject_wheel

%install
rm -rf %{buildroot}
# Installer le wheel sans ses dépendances
pip3 install --no-deps --root %{buildroot} --prefix /usr %{_sourcedir}/wapiti_swagger-0.1.9-py3-none-any.whl

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/wapiti_swagger*

%changelog
* Mon Oct 06 2025 Nicolas Surribas <nicolas.surribas@gmail.com> - 0.1.9
- Initial RPM packaging

