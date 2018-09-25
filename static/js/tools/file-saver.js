function download(filename, text, mimetype) {
  var element = document.createElement('a');
  element.setAttribute('href', 'data:'+mimetype+';charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}
