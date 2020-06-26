/opt/irods-externals/clang6.0-0/bin/clang++			\
	-I /opt/irods-externals/json3.7.3-0/include/         	\
        -stdlib=libc++						\
	-Wl,-rpath=/opt/irods-externals/clang-runtime6.0-0/lib $*
