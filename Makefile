clean:
	-find -name \*.pyc | parallel --gnu rm

test:
	nosetests
