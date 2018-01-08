#include "tsdb_api.h"

//#define assert_int_equal(expected, actual) do {assert_int_equal_log(expected, actual, __FUNCTION__, __LINE__);} while (0)

void assert_int_equal(expected, actual) {
	if (expected != actual) {
		char s[1000];
		sprintf(s, "Expected %d but was %d", expected, actual);
		printf("%-30s Line %-5d %s\r\n", __FUNCTION__, __LINE__, s);
		exit(1);
	}
}

void assert_int_equal_log(int expected, int actual, const char* function, unsigned int line) {
	char s[1000];
	sprintf(s, "Expected %d but was %d", expected, actual);
	if (expected != actual) {
		printf("%-30s Line %-5d %s\r\n", function, line, s);
	}
#ifdef EXIT_ON_FAIL
    exit(1);
#endif
}

int file_exists(char *filename) {
    FILE *file;
    if ((file = fopen(filename, "r"))) {
        fclose(file);
        return 1;
    } else {
        return 0;
    }
}

void print_usage() {
	fprintf(stderr, "usage examples:\n");
	fprintf(stderr, "help:\n -h\n");
	fprintf(stderr, "populate epoch:\n [-d <debug level>] -s <slot_seconds> -f <TEST-DB> -t <timestamp> -N <number of key-value pairs> <data file name>\n");
	fprintf(stderr, " in case d option will not be set - all output will be printed to stdout\n\n");
	fprintf(stderr, "get single key:\n  -s <slot_seconds> -f <TEST-DB> -t <timestamp> -g <key>\n");
	fprintf(stderr, "get Range of keys:\n -s <slot_seconds> -f <TEST-DB> -R <key> <start> <end> <interval>\n");
    exit(1);
}

int main(int argc, char *argv[]) {
    tsdb_handler db;
    int val, ret, num_keys, size, len, slot_seconds = 0;
	u_int32_t timestamp, start, end;
    char *cp, *name, *file, *key, line[100];
	u_int16_t vals_per_entry = 1;
	tsdb_value write_val, *read_val; 
	FILE *fp;
	
	if (argc < 4) {
        print_usage();
		exit(1);
    }
	name = argv[0];
	argc--, argv++;
	while (argc > 0) {
		if (**argv == '-') {
			cp = &argv[0][1];
			switch(*cp) {
			case 's':
				argv++;
				argc--;
				slot_seconds = atoi(*argv);
				break;
			case 'f':
				argv++;
				argc--;
				file = *argv;
			/* 
			   if (file_exists(file)) {
			        trace_error("%s DB doesn't exist", file);
			    }
			*/
				if (slot_seconds == 0) {
					print_usage();
					exit(1);
				}
				ret = tsdb_open(file, &db, &vals_per_entry, slot_seconds, 0);
				assert_int_equal(0, ret);
				break;
			case 'd':
				argv++;
				argc--;
				val = atoi(*argv);
				trace_log_file_open(); // TODO where I close it?
			    set_trace_level(val);
				if (val > 0 && val < 10) {
					set_trace_level(val);
					trace_info("debug level set to %d", val);
				} else {
					trace_info("Illegal debug level, not set");
				}
				break;
			case 't':
				argv++;
				argc--;
				timestamp = (unsigned) atoi(*argv);
				trace_info("timestamp[%d]", timestamp);
				ret = tsdb_goto_epoch(&db, timestamp, 0, 1);
				assert_int_equal(0, ret);
				break;
			case 'g':
				argv++;
				argc--;
				key = (char*)strdup(*argv);
				ret = tsdb_get_by_key(&db, key, &read_val);
			    assert_int_equal(0, ret);
				trace_error("key[%s] val[%d]", key, *read_val);
				break;
			case 'N':
				argv++;
				argc--;
				num_keys = atoi(*argv);

				argv++;
				argc--;
				file = *argv;

				trace_info("num_pairs[%d] in metric file[%s]", num_keys, file);

				fp = fopen(file, "r");
				if (fp == NULL) {
		           trace_error("metrics file wasn't found");
				   break;
       			}
				len = 200;

				while(fscanf(fp,"%s\n", line) != EOF) {
					name = strchr(line, '=');
					size = name - line;
					write_val = atoi(++name);
					*(line + size) = '\0';
					key = line;
					printf("key[%s] write_val[%d] size[%d]\n", key, write_val, size);

					if (size < 30) {
						trace_info("key[%s] val[%d]", key, write_val);
						ret = tsdb_set(&db, key, &write_val);
						assert_int_equal(0, ret);
						ret = tsdb_get_by_key(&db, key, &read_val);
						assert_int_equal(0, ret);
						assert_int_equal(write_val, *read_val);
					} else {
						trace_info("key[%s] size[%d] is to big - need to reduce", key, size);
					}
				}
				
				fclose(fp);
				break;
			case 'R':
				argv++;
				argc--;
				key = (char*)strdup(*argv); // <key> <start> <end>
				argv++;
				argc--;
				start = (unsigned) atol(*argv);
				argv++;
				argc--;
				end = (unsigned) atol(*argv);
				
				timestamp = start;
				// handle errors in case of wrong parameters
			    while (timestamp <= end) {
					ret = tsdb_goto_epoch(&db, timestamp, 0, 1);
					assert_int_equal(0, ret);
					if (!ret) {
						ret = tsdb_get_by_key(&db, key, &read_val);
						if (!ret) {
					        printf("%d,%d\n", timestamp, *read_val);
					    }
				    }
			        timestamp += slot_seconds;
			    }
				break;
			case 'h':
			default:
				print_usage();
			}
		}
		argv++;
		argc--;
	}
    tsdb_flush(&db);	
    tsdb_close(&db);
    return 0;
}

