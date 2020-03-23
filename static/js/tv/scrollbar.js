(function(w, d) {
  var raf = w.requestAnimationFrame || w.setImmediate || function(c) { return setTimeout(c, 0); };

  function initElX(el) {
    if (Object.prototype.hasOwnProperty.call(el, 'data-scrollbar-x')) return;
    Object.defineProperty(el, 'data-scrollbar-x', new ScrollBarX(el));
  }
  
  function initElY(el) {
    if (Object.prototype.hasOwnProperty.call(el, 'data-scrollbar-y')) return;
    Object.defineProperty(el, 'data-scrollbar-y', new ScrollBarY(el));
  }


  // Mouse drag handler
  function dragDealerX(el, context) {
    var lastPageX;

    el.addEventListener('mousedown', function(e) {
      lastPageX = e.pageX;
      el.classList.add('grabbed-sb');
      d.body.classList.add('grabbed-sb');

      d.addEventListener('mousemove', dragX);
      d.addEventListener('mouseup', stop);

      return false;
    });

    function dragX(e) {
      var delta = e.pageX - lastPageX;
      lastPageX = e.pageX;

      raf(function() {
        context.el.scrollLeft += delta / context.scrollRatio;
      });
    }

    function stop() {
      el.classList.remove('grabbed-sb');
      d.body.classList.remove('grabbed-sb');
      d.removeEventListener('mousemove', dragX);
      d.removeEventListener('mouseup', stop);
    }
  }

  function dragDealerY(el, context) {
 	var lastPageY;
 
    el.addEventListener('mousedown', function(e) {
      lastPageY = e.pageY;
      el.classList.add('grabbed-sb');
      d.body.classList.add('grabbed-sb');

      d.addEventListener('mousemove', dragY);
      d.addEventListener('mouseup', stop);

      return false;
    });

    function dragY(e) {
      var delta = e.pageY - lastPageY;
      lastPageY = e.pageY;

      raf(function() {
        context.el.scrollTop += delta / context.scrollRatio;
      });
    }

    function stop() {
      el.classList.remove('grabbed-sb');
      d.body.classList.remove('grabbed-sb');
      d.removeEventListener('mousemove', dragY);
      d.removeEventListener('mouseup', stop);
    }
  }

  // Constructor
  function sx(el) {
    this.target = el;

    this.direction = w.getComputedStyle(this.target).direction;

    this.bar = '<div class="scrollbar-x"><div class="scroll-x">';

    this.wrapper = d.createElement('div');
    this.wrapper.setAttribute('class', 'wrapper-sb');

    this.el = d.createElement('div');
    this.el.setAttribute('class', 'content-x');

    if (this.direction === 'rtl') {
      this.el.classList.add('rtl');
    }

    this.wrapper.appendChild(this.el);

    while (this.target.firstChild) {
      this.el.appendChild(this.target.firstChild);
    }
    this.target.appendChild(this.wrapper);

    this.target.insertAdjacentHTML('beforeend', this.bar);
    this.bar = this.target.lastChild.lastChild;

    dragDealerX(this.bar, this);
    this.moveBar();

    w.addEventListener('resize', this.moveBar.bind(this));
    this.el.addEventListener('scroll', this.moveBar.bind(this));
    w.addEventListener('update', this.moveBar.bind(this));

    this.target.classList.add('container-x');

    var css = w.getComputedStyle(el);
  	if (css.width === '0px' && css.maxWidth !== '0px') {
    	el.style.width = css['max-width'];
    }
  }

  sx.prototype = {
    moveBar: function(e) {
      var totalWidth = this.el.scrollWidth,
          ownWidth = this.el.clientWidth,
          _this = this;

      this.scrollRatio = ownWidth / totalWidth;

      raf(function() {
        // Hide scrollbar if no scrolling is possible
        if(_this.scrollRatio >= 1) {
          _this.bar.parentNode.classList.add('hidden-sb');
        } else {
          _this.bar.parentNode.classList.remove('hidden-sb');
          _this.bar.style.cssText = 'width:' + Math.max(_this.scrollRatio * 100, 10) + '%; left:' + (_this.el.scrollLeft / totalWidth ) * 100 + '%;';
        }
      });
    }
  };
  
  function sy(el) {
    this.target = el;

    this.direction = w.getComputedStyle(this.target).direction;

    this.bar = '<div class="scrollbar-y"><div class="scroll-y">';

    this.wrapper = d.createElement('div');
    this.wrapper.setAttribute('class', 'wrapper-sb');

    this.el = d.createElement('div');
    this.el.setAttribute('class', 'content-y');

    if (this.direction === 'rtl') {
      this.el.classList.add('rtl');
    }

    this.wrapper.appendChild(this.el);

    while (this.target.firstChild) {
      this.el.appendChild(this.target.firstChild);
    }
    this.target.appendChild(this.wrapper);

    this.target.insertAdjacentHTML('beforeend', this.bar);
    this.bar = this.target.lastChild.lastChild;

    dragDealerY(this.bar, this);
    this.moveBar();

    w.addEventListener('resize', this.moveBar.bind(this));
    this.el.addEventListener('scroll', this.moveBar.bind(this));
    w.addEventListener('update', this.moveBar.bind(this));

    this.target.classList.add('container-y');

    var css = w.getComputedStyle(el);
  	if (css.height === '0px' && css.maxHeight !== '0px') {
    	el.style.height = css['max-height'];
    }
  }

  sy.prototype = {
    moveBar: function(e) {
      var totalHeight = this.el.scrollHeight,
          ownHeight = this.el.clientHeight,
          _this = this;

      this.scrollRatio = ownHeight / totalHeight;

      raf(function() {
        // Hide scrollbar if no scrolling is possible
        if(_this.scrollRatio >= 1) {
          _this.bar.parentNode.classList.add('hidden-sb');
        } else {
          _this.bar.parentNode.classList.remove('hidden-sb');
          _this.bar.style.cssText = 'height:' + Math.max(_this.scrollRatio * 100, 10) + '%; top:' + (_this.el.scrollTop / totalHeight ) * 100 + '%;';
        }
      });
	  }
  };

  function initAll() {
    var nodes = d.querySelectorAll('*[scrollable-x]');

    for (let i = 0; i < nodes.length; i++) {
      initElX(nodes[i]);
    }
	
	nodes = d.querySelectorAll('*[scrollable-y]');

    for (let i = 0; i < nodes.length; i++) {
      initElY(nodes[i]);
    }

  }

  d.addEventListener('DOMContentLoaded', initAll);
  sx.initEl = initElX;
  sy.initEl = initElY;
  sx.initAll = initAll;
  sy.initAll = initAll;

  w.ScrollBarX = sx;
  w.ScrollBarY = sy;
})(window, document);