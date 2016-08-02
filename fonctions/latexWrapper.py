import os

from subprocess import call
from tempfile import mkdtemp, mkstemp

from django.template.loader import render_to_string

generate_pdf(template_path, template_variable, dest_name, dest_folder):
	# Get some temp files
	tmp_folder = mkdtemp()
	os.chdir(tmp_folder)
	texfile, texfilename = mkstemp(dir=tmp_folder)

	# Render to template with var
	os.write(texfile, render_to_string(template_path, template_variables))
	os.close(texfile)

	# Compile the TeX file with PDFLaTeX
	call(['pdflatex', texfilename])

	# Make pdf permanent
	os.rename(texfilename + '.pdf', os.path.join(dest_folder, dest_name + '.pdf'))

	# Cleanup
	os.remove(texfilename)
	os.remove(texfilename + '.aux')
	os.remove(texfilename + '.log')
	os.rmdir(tmp_folder)
	return os.path.join(dest_folder, dest_name + '.pdf')