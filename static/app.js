(function(){
  // theme
  var tt=document.getElementById('theme-toggle');
  if(tt)tt.addEventListener('click',function(){
    var cur=document.documentElement.dataset.theme||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
    var next=cur==='dark'?'light':'dark';document.documentElement.dataset.theme=next;
    try{localStorage.setItem('theme',next)}catch(e){}
  });

  // generic list filter (pals page + passives page)
  function hook(inputId,rows,getText){
    var inp=document.getElementById(inputId);if(!inp)return;
    inp.addEventListener('input',function(){var q=inp.value.trim().toLowerCase();var n=0;
      rows.forEach(function(r){var ok=!q||getText(r).indexOf(q)>=0;r.hidden=!ok||r.dataset.elhide==='1';if(!r.hidden)n++});
      var nm=document.getElementById('nomatch');if(nm)nm.hidden=n>0;});
  }
  var cards=[].slice.call(document.querySelectorAll('.palcard'));
  if(cards.length){
    hook('pal-filter',cards,function(c){return c.dataset.name});
    var active=null;
    document.querySelectorAll('.filter').forEach(function(b){b.addEventListener('click',function(){
      active=active===b.dataset.el?null:b.dataset.el;
      document.querySelectorAll('.filter').forEach(function(x){x.classList.toggle('on',x.dataset.el===active)});
      cards.forEach(function(c){c.dataset.elhide=(active&&c.dataset.els.split(' ').indexOf(active)<0)?'1':'0'});
      document.getElementById('pal-filter').dispatchEvent(new Event('input'));
    })});
  }
  var prow=[].slice.call(document.querySelectorAll('#passives tbody tr'));
  if(prow.length)hook('passive-filter',prow,function(r){return r.textContent.toLowerCase()});

  // calculator
  var panelPair=document.getElementById('panel-pair');if(!panelPair)return;
  var D=null,P=[],bySlug={};
  var sel={a:null,b:null,c:null,f:null};
  function el(tag,cls,html){var e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;return e}
  function avatar(p,size){return '<img class="avatar avatar-'+(size||'md')+' el-'+p.e[0].toLowerCase()+'" src="/img/pals/'+p.s+'.png" alt="" width="128" height="128" loading="lazy" decoding="async">'}
  function chip(p,size){return '<a class="palchip" href="/pal/'+p.s+'/">'+avatar(p,size)+'<span class="palchip-text"><b>'+p.n+'</b><small>#'+p.num+'</small></span></a>'}
  function esc(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}

  function setupPicker(box){
    var key=box.dataset.picker,inp=box.querySelector('input'),list=box.querySelector('.suggest'),clr=box.querySelector('.clear');
    var items=[],cursor=-1;
    function render(q){
      q=q.trim().toLowerCase();
      items=P.filter(function(p){return !q||p.n.toLowerCase().indexOf(q)>=0||p.s.indexOf(q.replace(/\s+/g,'-'))>=0}).slice(0,40);
      // starts-with first
      items.sort(function(x,y){var xs=x.n.toLowerCase().indexOf(q)===0?0:1,ys=y.n.toLowerCase().indexOf(q)===0?0:1;return xs-ys});
      list.innerHTML=items.map(function(p,i){return '<li role="option" data-i="'+i+'">'+avatar(p,'sm')+'<span>'+esc(p.n)+'</span><small>#'+p.num+'</small></li>'}).join('');
      list.hidden=items.length===0;inp.setAttribute('aria-expanded',String(!list.hidden));cursor=-1;
    }
    function choose(p){sel[key]=p;inp.value=p?p.n:'';box.classList.toggle('has-value',!!p);list.hidden=true;inp.setAttribute('aria-expanded','false');update(true)}
    inp.addEventListener('input',function(){sel[key]=null;box.classList.remove('has-value');render(inp.value)});
    inp.addEventListener('focus',function(){render(inp.value);inp.select()});
    inp.addEventListener('keydown',function(e){
      if(list.hidden&&(e.key==='ArrowDown'))render(inp.value);
      if(e.key==='ArrowDown'){cursor=Math.min(cursor+1,items.length-1);mark();e.preventDefault()}
      else if(e.key==='ArrowUp'){cursor=Math.max(cursor-1,0);mark();e.preventDefault()}
      else if(e.key==='Enter'){if(items.length){choose(items[cursor>=0?cursor:0])}e.preventDefault()}
      else if(e.key==='Escape'){list.hidden=true}
    });
    function mark(){[].forEach.call(list.children,function(li,i){li.setAttribute('aria-selected',String(i===cursor));if(i===cursor)li.scrollIntoView({block:'nearest'})})}
    list.addEventListener('mousedown',function(e){var li=e.target.closest('li');if(li){choose(items[+li.dataset.i]);e.preventDefault()}});
    inp.addEventListener('blur',function(){setTimeout(function(){list.hidden=true;if(!sel[key]&&inp.value){var m=P.filter(function(p){return p.n.toLowerCase()===inp.value.trim().toLowerCase()});if(m[0])choose(m[0])}},120)});
    clr.addEventListener('click',function(){choose(null);inp.focus()});
    box._choose=choose;
  }
  var pickers={};document.querySelectorAll('.picker').forEach(function(b){setupPicker(b);pickers[b.dataset.picker]=b});

  var tabs=document.querySelectorAll('.tab'),mode='pair';
  function setMode(m,push){mode=m;tabs.forEach(function(t){var on=t.id==='tab-'+m;t.classList.toggle('active',on);t.setAttribute('aria-selected',String(on))});
    document.getElementById('panel-pair').hidden=m!=='pair';document.getElementById('panel-child').hidden=m!=='child';if(push!==false)update(true)}
  tabs.forEach(function(t){t.addEventListener('click',function(){setMode(t.id.replace('tab-',''))})});
  document.getElementById('swap').addEventListener('click',function(){var a=sel.a,b=sel.b;pickers.a._choose(b);pickers.b._choose(a)});

  function isSpecial(i,j){var lo=Math.min(i,j),hi=Math.max(i,j);return D.specialSet[lo+','+hi]}
  function genderRule(i,j){return D.gender.filter(function(g){return (g[0]===i&&g[1]===j)||(g[0]===j&&g[1]===i)})}

  function update(pushUrl){
    if(!D)return;
    var q=new URLSearchParams();
    if(mode==='pair'){
      var out=document.getElementById('pair-result');out.innerHTML='';
      if(sel.a)q.set('a',sel.a.s);if(sel.b)q.set('b',sel.b.s);
      if(sel.a&&sel.b){
        var i=sel.a.i,j=sel.b.i,c=D.child[i][j];
        var rules=genderRule(i,j);
        if(rules.length){
          out.innerHTML=rules.map(function(g){var pa=P[g[0]],pb=P[g[1]],pc=P[g[2]];return '<div class="result-child">'+chip(pa,'lg')+'<span class="muted">('+g[3]+')</span><span class="arrow">+</span>'+chip(pb,'lg')+'<span class="muted">('+g[4]+')</span><span class="arrow">→</span><span class="big">'+chip(pc,'lg')+'</span></div>'}).join('')+'<p class="note">Gender matters for this pair: the child depends on which parent is female.</p>';
        } else if(c>=0){
          var pc=P[c];
          out.innerHTML='<div class="result-child">'+chip(sel.a,'lg')+'<span class="arrow">+</span>'+chip(sel.b,'lg')+'<span class="arrow">→</span><span class="big">'+chip(pc,'lg')+'</span>'+(isSpecial(i,j)?'<span class="badge">special combo</span>':'')+'</div>'
            +'<p class="small"><a href="/pal/'+pc.s+'/">All ways to breed '+esc(pc.n)+'</a>'+(D.popular[sel.a.s]&&D.popular[sel.b.s]?' · <a href="/breed/'+(D.popular[sel.a.s]<=D.popular[sel.b.s]?sel.a.s+'/'+sel.b.s:sel.b.s+'/'+sel.a.s)+'/">Permalink</a>':'')+'</p>';
          document.title=sel.a.n+' + '+sel.b.n+' = '+pc.n+' · Palworld Breeding Calculator';
        } else out.innerHTML='<p class="result-empty">No result for this pair.</p>';
      } else if(sel.a||sel.b){
        var p=sel.a||sel.b,i2=p.i;
        var rows=P.map(function(o){var c=D.child[i2][o.i];return c<0?'':'<div class="combo">'+chip(o,'sm')+'<span class="plus">→</span>'+chip(P[c],'sm')+'</div>'}).join('');
        out.innerHTML='<p class="muted small">Pick a second parent, or browse what '+esc(p.n)+' breeds with every Pal:</p><div class="combo-list">'+rows+'</div>';
      } else out.innerHTML='<p class="result-empty">Pick two parents to see their child.</p>';
    } else {
      var out2=document.getElementById('child-result');out2.innerHTML='';
      if(sel.c)q.set('child',sel.c.s);if(sel.f)q.set('with',sel.f.s);
      if(sel.c){
        var t=sel.c.i,list=[];
        for(var x=0;x<P.length;x++)for(var y=x;y<P.length;y++)if(D.child[x][y]===t){if(sel.f&&x!==sel.f.i&&y!==sel.f.i)continue;list.push([x,y])}
        D.gender.forEach(function(g){if(g[2]===t&&!(sel.f&&g[0]!==sel.f.i&&g[1]!==sel.f.i))list.push([g[0],g[1],g[3],g[4]])});
        if(!list.length)out2.innerHTML='<p class="result-empty">No pair breeds '+esc(sel.c.n)+(sel.f?' with '+esc(sel.f.n):'')+'. It must be caught or hatched from a wild egg.</p>';
        else out2.innerHTML='<p><b>'+list.length+'</b> parent pair'+(list.length===1?'':'s')+' breed '+chip(sel.c,'sm')+(sel.f?' using '+esc(sel.f.n):'')+'. <a class="small" href="/pal/'+sel.c.s+'/">Open the '+esc(sel.c.n)+' page</a></p><div class="combo-list">'
          +list.map(function(pr){return '<div class="combo">'+chip(P[pr[0]],'sm')+(pr[2]?'<small class="muted">('+pr[2]+')</small>':'')+'<span class="plus">+</span>'+chip(P[pr[1]],'sm')+(pr[3]?'<small class="muted">('+pr[3]+')</small>':'')+(isSpecial(pr[0],pr[1])&&!pr[2]?'<span class="badge">special</span>':'')+'</div>'}).join('')+'</div>';
        document.title='How to breed '+sel.c.n+' · Palworld Breeding Calculator';
      } else out2.innerHTML='<p class="result-empty">Pick the Pal you want to breed.</p>';
    }
    if(pushUrl){var s=q.toString();history.replaceState(null,'',s?'/?'+s:'/')}
  }

  fetch('/data.json').then(function(r){return r.json()}).then(function(d){
    D=d;P=d.pals.map(function(p,i){p.i=i;bySlug[p.s]=p;return p});
    D.specialSet={};d.special.forEach(function(x){D.specialSet[x[0]+','+x[1]]=true});
    var q=new URLSearchParams(location.search);
    function pick(k,v){if(v&&bySlug[v]){sel[k]=bySlug[v];pickers[k].querySelector('input').value=bySlug[v].n;pickers[k].classList.add('has-value')}}
    pick('a',q.get('a'));pick('b',q.get('b'));pick('c',q.get('child'));pick('f',q.get('with'));
    setMode(q.get('child')?'child':'pair',false);update(false);
  });
})();
// Ad rails: only request ads once real slot IDs are configured (after AdSense approval).
(function(){var ins=document.querySelectorAll('.adrail ins.adsbygoogle');ins.forEach(function(el){if(/^\d+$/.test(el.getAttribute('data-ad-slot')||'')){try{(adsbygoogle=window.adsbygoogle||[]).push({})}catch(e){}}})})();
