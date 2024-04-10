import os
from pygments import lexers

def get_subpath(snapshotpath, datatype):
	"""
	Returns the subpath within a given snapshot path that contains a specific datatype.
	
	:param snapshotpath: The path to the snapshot directory where the data is stored.
	:param datatype: A string that represents the specific datatype within the snapshot path.
	:returns: the required subpath
	"""
	
	datasubpath = next(subpath for subpath in os.listdir(snapshotpath) if datatype in subpath) 
	return os.path.join(snapshotpath, datasubpath)


def get_content_from_patch(patch, version):
	"""
	This functions extracts the code file's content from a patch file based on the specified file
	version.
	
	:param patch: A string that represents the patch of a GitHub's commit for a file. 
	It follows the unified diff format, which shows the differences between two versions of a file
	:param version: A string used to specify which version of the file's content to
	retrieve from the patch. It can have two possible values: 'current' or 'previous'
	:returns: the content of the file based on the given patch and version.
	"""

	patch_lines = patch.splitlines()
	content_lines = []

	if version == 'current':
		# Specify which patch lines belongs to current version of the file
		for line in patch_lines:
			if line[0] == '+':
				content_lines.append(line[1:])
			elif line[0] != '@' and line[0] != '-':
				content_lines.append(line)

	elif version == 'previous':
		# Specify which patch lines belongs to previous version of the file
		for line in patch_lines:
			if line[0] == '-':
				content_lines.append(line[1:])
			elif line[0] != '@' and line[0] != '+':
				content_lines.append(line)

	content = '\n'.join(content_lines)
	return content


def get_file_extension(filename):
	"""
	This function attempts to determine the file extension of a given filename by
	using the `get_lexer_for_filename` function from the `lexers` module.
	
	:param filename: A string that represents the name of a file, including its extension
	:returns: The file extension of the given filename if it can be determined by the `lexers` module. 
	If the file extension cannot be determined or an exception occurs, it returns `None`.
	"""

	try:
		lexer = lexers.get_lexer_for_filename(filename)
		return lexer.filenames[0]
	except Exception as e:
		return None
