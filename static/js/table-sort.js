const getCellValue = (tr, idx) => tr.children[idx].dataset.value || tr.children[idx].innerText || tr.children[idx].textContent;

const comparer = (idx, asc) => (a, b) =>
  ((v1, v2) => 
     v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
  )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

[...document.getElementsByTagName('table')].forEach(table =>
{
  const tbody = table.getElementsByTagName('tbody')[0];
  table.querySelectorAll('th.sort').forEach(th =>
  {
    th.addEventListener('click', (() =>
    {
      th.asc = !th.asc;
      console.warn(table);
      table.querySelectorAll('th.sort').forEach(e =>
      {
        e.classList.remove('asc');
        e.classList.remove('desc');
      });
      th.asc ? th.classList.add('asc') : th.classList.add('desc');
      [...tbody.querySelectorAll('tr')].sort(comparer(Array.from(th.parentNode.children).indexOf(th), th.asc)).forEach(tr => tbody.appendChild(tr) );
    }));
    th.innerHTML += '<i aria-hidden="true" class="fa fa-fw sort"></i>';
  });
});
