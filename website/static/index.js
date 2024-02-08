inp=document.getElementById('hamburger-menu-input')
let sidebardisplay=0;
inp.addEventListener('click',function(){
  sidebar=document.getElementsByClassName('sidebar')[0];
  sidebardisplay=1-sidebardisplay;
  if(sidebardisplay==0)
    sidebar.style.display='none';
  else
    sidebar.style.display='block';
})