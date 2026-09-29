const dlg=document.querySelector('#lightbox');
document.querySelectorAll('.zoom').forEach(b=>b.addEventListener('click',ev=>{
 ev.preventDefault();dlg.querySelector('img').src=b.dataset.img;
 dlg.querySelector('p').textContent=b.dataset.caption||'';dlg.showModal();
}));
dlg.querySelector('.close').onclick=()=>dlg.close();
dlg.addEventListener('click',ev=>{if(ev.target===dlg)dlg.close();});
