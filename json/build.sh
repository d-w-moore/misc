/opt/irods-externals/clang6.0-0/bin/clang++			\
	-I /opt/irods-externals/json3.7.3-0/include/         	\
	-I /opt/irods-externals/jansson2.7-0/include/		\
	-L /opt/irods-externals/jansson2.7-0/lib/		\
        -stdlib=libc++	-ljansson				\
	-Wl,-rpath=/opt/irods-externals/clang-runtime6.0-0/lib:/opt/irods-externals/jansson2.7-0/lib $*
