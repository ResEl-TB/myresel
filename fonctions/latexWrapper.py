import os

from subprocess import call
from tempfile import mkdtemp, mkstemp
from shutil import copyfile

from django.template.loader import render_to_string


def generate_pdf(template_path, template_variable, dest_name, dest_folder):
    """
    Ex :
    generate_pdf('tresorerie/facture.tex', {'confLang': 'fr', 'user': {'uid': 'tjacquin', 'firstName':'Théo', 'lastName': 'Jacquin', 'addressFirstPart': '3 rue Coquelicot', 'addressSecondPart': '97345 Guyane'}, 'invoice': {'id': 1234567, 'date':'\\today', 'internetFeesPrice': '84.5', 'isPaid':'yes', 'payment': {'date':'\\today', 'info': 'Carte Bleue, virement n 3456765432'}}}, 'test_facture', '/srv/www/resel.fr/media/invoices')
    """
    # Get some temp files
    tmp_folder = mkdtemp()
    os.chdir(tmp_folder)
    texfile, texfilename = mkstemp(dir=tmp_folder)

    # Render to template with var
    os.write(texfile, render_to_string(template_path, template_variable).encode('utf-8'))
    os.close(texfile)

    # Compile the TeX file with PDFLaTeX
    call(['pdflatex', '-interaction=batchmode', texfilename])

    # Make pdf permanent
    # TODO : improve handle errors !
    copyfile(texfilename + '.pdf', os.path.join(dest_folder, dest_name + '.pdf'))

    # Cleanup
    os.remove(texfilename)
    os.remove(texfilename + '.pdf')
    os.remove(texfilename + '.aux')
    os.remove(texfilename + '.log')
    os.rmdir(tmp_folder)
    return os.path.join(dest_folder, dest_name + '.pdf')
