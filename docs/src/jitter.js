// 把 .cut 元素的邊緣做成「剪刀剪過」的不規則多邊形（固定種子，每次渲染一樣）
(function(){
  let s=20261111; const rnd=()=> (s=(s*1664525+1013904223)>>>0)/4294967296;
  document.querySelectorAll('.cut').forEach(el=>{
    const w=el.offsetWidth,h=el.offsetHeight,j=+(el.dataset.j||0),pts=[]; const step=+(el.dataset.step||46);
    const edge=(x0,y0,x1,y1)=>{const n=Math.max(1,Math.round(Math.hypot(x1-x0,y1-y0)/step));for(let i=0;i<n;i++){const t=i/n;pts.push([x0+(x1-x0)*t+(rnd()-.5)*2*j,y0+(y1-y0)*t+(rnd()-.5)*2*j])}};
    if(el.dataset.shape==='arrow'){ // 向右的粗箭頭
      const a=h*0.55,b=h*0.3; const L=[[0,h*0.5-b],[w-a,h*0.5-b],[w-a,0],[w,h*0.5],[w-a,h],[w-a,h*0.5+b],[0,h*0.5+b]];
      for(let i=0;i<L.length;i++){const p=L[i],q=L[(i+1)%L.length];edge(p[0],p[1],q[0],q[1])}
    } else { edge(0,0,w,0);edge(w,0,w,h);edge(w,h,0,h);edge(0,h,0,0) }
    if(!j && el.dataset.shape!=='arrow') return;
    el.style.clipPath='polygon('+pts.map(p=>p[0].toFixed(1)+'px '+p[1].toFixed(1)+'px').join(',')+')';
  });
})();
