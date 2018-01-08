CC           = gcc -g
CFLAGS       = -Wall -I. -DEXIT_ON_FAIL
LDFLAGS      = -L /opt/local/lib
SYSLIBS      = -ldb

TSDB_LIB     = libtsdb.a
TSDB_LIB_O   = tsdb_api.o tsdb_trace.o tsdb_bitmap.o quicklz.o

TARGETS      = $(TSDB_LIB) \
				tsdb-tool
			   
all: $(TARGETS)

%.o: %.c %.h
	${CC} ${CFLAGS} ${INCLUDE} -c $< -o $@

$(TSDB_LIB): $(TSDB_LIB_O)
	ar rs $@ ${TSDB_LIB_O}
	ranlib $@

tsdb-%: tsdb_%.o $(TSDB_LIB)
	$(CC) $(LDFLAGS) tsdb_$*.o $(TSDB_LIB) $(SYSLIBS) -o $@

clean:
	rm -f ${TARGETS} *.o *~
