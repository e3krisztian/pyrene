.PHONY: all clean test

all: clean test

clean:
	-find -name \*.pyc | parallel --gnu rm

test:
	nosetests
