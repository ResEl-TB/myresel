/**
 * Returns whether an element overflows its container. It both checks if the text overflows (if it
 * is in a normal flow, that is static or relative) or if it is larger than the regular container
 * (if it is out of the normal flow, e.g. absolutely-positioned).
 *
 * @param {Element} el - The element to check
 * @returns {Boolean} Whether the element overflows
 */
function overflows(el)
{
    return el.scrollWidth > el.offsetWidth || parseFloat(window.getComputedStyle(el).width) > parseFloat(window.getComputedStyle(el.parentNode).width);
}


/**
 * Formats ``hours`` and ``minutes`` to a more human ``hh``:``mm``.
 *
 * @param {Number} hours - The hours to convert
 * @param {Number} minutes - The minutes to convert
 * @returns {String} Colon-separated time
 */
function formatTime(hours, minutes)
{
    var str = "";
    if (hours < 10)
        str += '0';
    str += `${hours}:`;
    if (minutes < 10)
        str += '0';
    return str + minutes;
}

/**
 * Converts two timestamps into an human-readable duration.
 *
 * @param {Number} start - The initial timestamp
 * @param {Number} end - The final timestamp
 * @param {Boolean} col - Whether the duration should be formatted with a colon (``hh``:``mm``)
 *                        or not (``hours`` h ``minutes`` min)
 * @returns {String} Formatted duration
 */
function displayDuration(start, end, col)
{
    if(!start || !end)
        return "Indisponible";
    var hours = Math.floor((end - start) / 3600);
    var minutes = Math.floor((end - start) / 60) % 60;
    let str = "";
    if (col)
        return formatTime(hours, minutes);
    if (hours)
    {
        str += `${hours} h`;
        if(minutes)
            str += ' ';
    }
    if (minutes)
        str += `${minutes} min`;
    return str;
}

/**
 * Converts a timestamp into an human-readable time.
 *
 * @param {Number} time - The timestamp
 * @returns {String} (``hh``:``mm``)-formatted duration
 */
function displayTime(time)
{
    var date = new Date(time * 1000);
    return formatTime(date.getHours(), date.getMinutes());
}

/**
 * Returns a time range in a human-readable format.
 *
 * @param {Number} time - The initial timestamp
 * @param {Number} time - The final timestamp
 * @returns {String} (De ``begin`` à ``end``)-formatted range
 */
function displayRange(start, end)
{
    if (end)
        return `De ${displayTime(start)} à ${displayTime(end)}`;
    else
        return "Durée indéterminée";
}


/**
 * Downloads a file, then executes the given callback with the JSON-parsed file.
 *
 * @param {String} url - The file URL
 * @param {Function} callback - The function to be called when the file has been loaded
 */
function ajaxGet(url, callback) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = () => {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            try {
                var data = JSON.parse(xmlhttp.responseText);
            } catch(err) {
                console.log(`${err.message} in ${xmlhttp.responseText}`);
                return;
            }
            callback(data);
        }
    };
 
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

/**
 * Class defining a TV program.
 *
 * @param {String} title - The program title
 * @param {String} subtitle - The program subtitle
 * @param {Number} start - The beginning timestamp
 * @param {Number} end - The end timestamp
 * @param {String} desc - The program description
 */
function Program(title, subtitle, start, end, desc)
{
    this.title = title;
    this.subtitle = subtitle;
    this.start = start;
    this.end = end;
    this.desc = desc;
}

/**
 * Class defining a TV channel.
 *
 * @param {Number} lcn - The logical channel number
 * @param {Number} sid - The MuMuDVB channel identifier
 */
function Channel(name, lcn, sid)
{
    this.name = name;
    this.lcn = lcn;
    this.sid = sid;
}


class ResElTV extends HTMLElement {
  constructor()
  {
    super();

    const shadow = this.attachShadow({mode: 'open'});

    // Create spans
    const container = document.createElement('div');
    container.id = 'container';
    container.innerHTML = `
    <div id="loading">
    <div id="logo">
      <svg viewBox="119 91.42 187.17 51" id="resel">
        <style>
          .a{
            fill:#FFF;
          }
        </style>
        <polygon points="298 142.42 119 142.42 119 91.42 306.17 91.42 "></polygon>
        <path d="M135.84 121.09L133.16 137h-8.97l6.68-39.99h14.8c3.73 0 6.61 0.41 8.63 1.22 2.02 0.81 3.61 2.2 4.78 4.16 1.16 1.96 1.74 4.03 1.74 6.19 0 2.33-0.7 4.54-2.09 6.65 -1.4 2.11-3.69 3.58-6.9 4.42L156.8 137h-9.34l-4.2-15.91H135.84zM138.52 104.01l-1.71 10.14h5.92c2.29 0 3.97-0.15 5.05-0.45s1.97-0.89 2.67-1.76c0.69-0.87 1.04-1.94 1.04-3.21 0-1.66-0.53-2.86-1.6-3.6 -1.06-0.74-2.84-1.11-5.31-1.11H138.52z" class="a"></path>
        <path d="M198.46 97.01l-1.29 7.59h-18.8l-1.37 8.2h15.72l-1.2 7.24h-15.73l-1.57 9.38h19.14L192.07 137h-28.48l6.68-39.99H198.46z" class="a"></path>
        <path d="M229.66 106.82l-8.2 1.9c-0.94-3.32-3.21-4.98-6.83-4.98 -1.68 0-3.01 0.4-4 1.2 -0.99 0.8-1.48 1.77-1.48 2.9 0 1.13 0.4 1.99 1.2 2.57 0.8 0.59 2.33 1.16 4.6 1.73 3.26 0.82 5.83 1.68 7.71 2.59 1.88 0.91 3.32 2.18 4.32 3.81s1.51 3.62 1.51 5.96c0 3.77-1.39 6.91-4.16 9.44s-6.72 3.79-11.84 3.79c-4.37 0-8.01-1.01-10.91-3.03 -2.9-2.02-4.7-5.06-5.4-9.13l8.56-1.17c0.88 3.97 3.58 5.95 8.12 5.95 2.05 0 3.62-0.44 4.72-1.31 1.09-0.88 1.64-1.99 1.64-3.33 0-1.28-0.42-2.21-1.25-2.79 -0.83-0.57-2.76-1.27-5.79-2.1 -2.75-0.73-4.94-1.53-6.58-2.41 -1.63-0.88-2.93-2.12-3.9-3.73 -0.97-1.61-1.45-3.45-1.45-5.52 0-3.38 1.28-6.35 3.84-8.93s6.08-3.86 10.58-3.86C222.39 96.37 227.39 99.85 229.66 106.82z" class="a"></path>
        <path d="M267.16 97.01l-1.29 7.59h-18.8l-1.37 8.2h15.72l-1.2 7.24h-15.73l-1.57 9.38h19.14L260.77 137h-28.48l6.68-39.99H267.16z" class="a"></path>
        <path d="M282.43 97.01l-5.41 32.4h15.75l-1.26 7.59h-24.93l6.68-39.99H282.43z" class="a"></path>
      </svg>
      <svg viewBox="226.4 157.7 70.5 42.7" id="tv">
        <path d="M257.7 165.8h-10.7l-5.8 34.6h-9.8l5.8-34.6h-10.7l1.3-8.1h31.3L257.7 165.8z"></path>
        <path d="M296.9 157.7l-19.6 42.7h-10.3l-6.3-42.7h9.8l4.1 31.9 13.8-31.9H296.9z"></path>
      </svg>
      <div id="loader-container"><div id="loader"></div></div>
    </div>
    </div>
      <div id="video">
        <div id="overlay">
          <div id="overlay-title"></div>
          <div id="separator"></div>
          <div id="overlay-page" class="container-y" scrollable-y>
            <div class="wrapper-sb">
              <div class="content-y">
                <div id="overlay-rating"></div>
                <div id="overlay-subtitle"></div>
                <div id="overlay-description"></div>
                <div id="overlay-time"></div>
              </div>
            </div>
            <div class="scrollbar-y hidden-sb">
              <div class="scroll-y"></div>
            </div>
          </div>
          <div id="videobar">
            <div class="progressbar">
              <div id="overlay-progress" class="progress"></div>
            </div>
            <div class="playpause-container">
              <div id="play-pause" class="overlay-button"></div>
            </div>
            <div id="sound-container">
              <svg id="sound" viewBox="0 0 297.6 290">
                <polygon points="0 95.4 0 194.6 66.1 194.6 148.8 277.3 148.8 12.7 66.1 95.4"></polygon>
                <path d="M223.2 145c0-28.8-16.9-53.9-41.3-66.1v132.3C206.4 199.9 223.2 174.3 223.2 145z" id="volume1"></path>
                <path d="M181.9 0v34.1c47.8 14.2 82.7 58.5 82.7 111S229.7 241.8 181.9 256v34.1c66.3-15 115.8-74.2 115.8-145S248.2 15 181.9 0z" id="volume2"></path>
              </svg>
              <input id="volume" value="100" type="range">
            </div>
            <div id="duration-indicator"></div>
              <svg id="fullscreen" class="overlay-button" viewBox="10 10 16 16">
                <path d="m10 16 2 0 0-4 4 0 0-2L10 10l0 6 0 0z"></path>
                <path d="m20 10 0 2 4 0 0 4 2 0L26 10l-6 0 0 0z"></path>
                <path d="m24 24-4 0 0 2L26 26l0-6-2 0 0 4 0 0z"></path>
                <path d="M12 20 10 20 10 26l6 0 0-2-4 0 0-4 0 0z"></path>
              </svg>
            </div>
          </div>
        <video preload="auto"></video>
      </div>
      <div id="channels"></div>
    `;

    const styleSheet = document.createElement('link');
    styleSheet.rel = 'stylesheet';
    styleSheet.href = 'style.css';
    
    const scrollbarStyleSheet = document.createElement('link');
    scrollbarStyleSheet.rel = 'stylesheet';
    scrollbarStyleSheet.href = 'scrollbar.css';

    shadow.appendChild(styleSheet);
    shadow.appendChild(scrollbarStyleSheet);
    shadow.appendChild(container);

    this.container = container;
    this.shadow = shadow;
    this.loadingDiv = shadow.getElementById("loading");
    this.videoDiv = shadow.getElementById("video");
    this.channelsDiv = shadow.getElementById("channels");

    /** Whether the client cursor is on an :ref:`Interactive Zone <interactive_zones>` or not. */
    this.interacting = 0;
	
    /** The interface state. ``0`` is to the Normal State, ``1`` is the Detailed State and ``2`` is the Expanded State. See :ref:`states` for further details. */
    this.state = 0;
	
    /** Timer until the :js:func:`expanded` function gets called. */
    this.mouseTimer = null;
	
    this.cursorVisible = true; // TODO: implement or remove

    /** The player channels list. */
    this.channels = [];


    /** The player volume. */
    this.volume = 100;

    /** The previous player volume. */
    this.previousVolume = 100;

    /** Whether the player is playing or paused. */
    this.playing = true;
	
    /** Whether the player has been fully initialized. */
    this.init = false;
	
    /** The Dash.js video player. */
    this.player = dashjs.MediaPlayer().create();
    this.player.initialize(this.videoDiv.querySelector("video"));

    ScrollBarX.initEl(this.channelsDiv);
    this.channelsDiv = this.channelsDiv.firstChild.firstChild;

    //-----
    
    this.channelsDiv.onmouseover = () => {
      this.interacting++;
    };

    this.channelsDiv.onmouseout = () => {
      this.interacting--;
    };

    this.shadow.getElementById('videobar').onmouseover = () => {
      this.interacting++;
    };

    this.shadow.getElementById('videobar').onmouseout = () => {
      this.interacting--;
    };

    var timer = (() => {
      if (this.mouseTimer)
      {
        window.clearTimeout(this.mouseTimer);
      }
          
      if (this.state == 2)
      {
        this.container.classList.remove("expanded");
        // this.container.className = "";
        this.state = 0;
      }
    
      if (this.state + this.interacting == 0)
        this.mouseTimer = window.setTimeout(this.expand.bind(this), 1000);
    }).bind(this);
    
    this.container.onmousemove = timer;
    this.container.onmouseup = timer;
    this.container.onmousedown = timer;

    var playPauseButton = this.shadow.getElementById("play-pause");
    playPauseButton.onclick = () => {this.playPause(playPauseButton)};
    var volumeSlider = this.shadow.getElementById("volume");
    volumeSlider.oninput = this.updateVolume(volumeSlider);
    volumeSlider.onchange = this.updateVolume(volumeSlider);
    volumeSlider.onmousedown = () => {if (volumeSlider.value > 0) this.previousVolume = volumeSlider.value};
    this.shadow.getElementById("sound").onclick = () => {this.switchVolume()};
    this.shadow.getElementById("fullscreen").onclick = () => {this.fullScreen().bind(this)};
    
    ajaxGet('https://tvapi.resel.fr/v0/channels', (data =>
    {
      for (var channel of data)
      {
        this.channelsDiv.insertAdjacentHTML('beforeend', `<div tabindex="0" class="channel" data-lcn="${channel.lcn}"><div class="flip"><div class="card"><div class="channel-logo" style="background-image: url('https://resel.fr/static/images/tv/channels/${channel.sid}.png');"></div><div class="channel-more"><div class="more-button"></div></div></div></div><div class="program"><div class="program-title"></div><div class="progressbar"><div class="progress"></div></div><div class="duration"></div></div><div class="middle"><div class="details"><div class="subtitle"></div><div class="rating"></div></div><div class="time"></div></div><div class="right"><div class="description"><p></p></div></div></div>`);
        channel.channelDiv = this.channelsDiv.lastChild;
        channel.channelDiv.onclick = this.switchChannel(channel);
        channel.channelDiv.querySelector(".description").onclick = e => {e.stopPropagation()};
        channel.channelDiv.querySelector(".channel-more").onclick = this.switchView(channel);
        ScrollBarY.initEl(channel.channelDiv.querySelector(".description"));
        
        this.channels.push(channel);
      }
      
      this.switchChannel(this.channels[0])();
      this.init = true;
      this.update();
    
      this.loadingDiv.classList.add("done");
      setTimeout((() => {
        this.container.removeChild(this.loadingDiv)
      }).bind(this), 1000);

      setInterval(this.update.bind(this), 20000);
      setInterval(this.softUpdate.bind(this), 2000);
    }).bind(this));
  }

  /**
   * Enters or leaves the fullscreen mode.
   */
  fullScreen()
  {
    var elem = this.container || document.documentElement;
    if (!document.fullscreenElement && !document.mozFullScreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement)
    {
      if (elem.requestFullscreen)
        elem.requestFullscreen();
      else if (elem.msRequestFullscreen)
        elem.msRequestFullscreen();
      else if (elem.mozRequestFullScreen)
        elem.mozRequestFullScreen();
      else if (elem.webkitRequestFullscreen)
        elem.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
      this.container.classList.add("fullscreen");
    }
    else
    {
      if (document.exitFullscreen)
        document.exitFullscreen();
      else if (document.msExitFullscreen)
        document.msExitFullscreen();
      else if (document.mozCancelFullScreen)
        document.mozCancelFullScreen();
      else if (document.webkitExitFullscreen)
        document.webkitExitFullscreen();
      this.container.classList.remove("fullscreen");
    }
  }

  /**
   * Updates the overlay with data regarding the given channel.
   *
   * @param {Channel} channel - The channel to load the data from
   */
  updateOverlay(channel)
  {
    var overlayTitle = this.shadow.getElementById("overlay-title");
    overlayTitle.innerHTML = channel.channelDiv.querySelector(".program-title").innerHTML;
    let subtitle = channel.channelDiv.querySelector(".subtitle").innerHTML;
    let subtitleDiv = this.shadow.getElementById("overlay-subtitle");
    subtitleDiv.innerHTML = subtitle;
    if (subtitle)
      subtitleDiv.style.display = "block";
    else
      subtitleDiv.style.display = "none";
    this.shadow.getElementById("overlay-rating").innerHTML = channel.channelDiv.querySelector(".rating").innerHTML;
    this.shadow.getElementById("overlay-description").innerHTML = channel.channelDiv.querySelector(".description p").innerHTML;
    this.shadow.getElementById("overlay-time").innerHTML = channel.channelDiv.querySelector(".time").innerHTML;
    this.shadow.getElementById("overlay-progress").style.width = channel.channelDiv.querySelector(".progress").style.width;
    this.shadow.getElementById("duration-indicator").innerHTML = `${displayDuration(channel.currentProgram.start, this.currentTime, true)} / ${displayDuration(channel.currentProgram.start, channel.currentProgram.end, true)}`;
    if (overflows(overlayTitle))
      overlayTitle.classList.add("overflow");
    else
      overlayTitle.classList.remove("overflow");
  }

  /**
   * Switches to another channel.
   *
   * @param {Channel} channel - The channel to switch to
   */
  switchChannel(channel)
  {
    return (() =>
    {
      this.container.classList.remove("detailed");
      if (this.init)
        this.currentChannel.channelDiv.classList.remove("active");
      channel.channelDiv.classList.remove("selected");
      channel.channelDiv.classList.add("active");
      this.currentChannel = channel;
      if (this.state)
      {
        var box = channel.channelDiv.getBoundingClientRect();
        this.channelsDiv.scrollLeft = box.x + (box.width - this.channelsDiv.clientWidth) * this.scrollRatio - parseFloat(window.getComputedStyle(channel.channelDiv).marginRight);
      }
      this.state = 0;
      this.player.attachSource(`https://tnt.resel.fr/play/dash/${channel.sid}/index.mpd`);
      if (this.init)
        this.updateOverlay(channel);
      window.dispatchEvent(new Event("update"));
    }).bind(this);
  }

  /**
   * Switches between :ref:`normal_state` and :ref:`detailed_state`.
   *
   * @param {Channel} channel - The channel whose details should be shown or hidden
   */
  switchView(channel)
  {
    return (e =>
    {
      e.stopPropagation();
      if(this.state)
      {
        this.container.classList.remove("detailed");
        channel.channelDiv.querySelector(".channel-more").style.visibility = "hidden";
        setTimeout((() => {channel.channelDiv.querySelector(".channel-more").style.visibility = ""}).bind(this), 200);
        channel.channelDiv.classList.remove("selected");
        this.state = 0;
        var coll = this.channelsDiv.children;
        for (let i = 0; i < coll.length; i++)
        {
          var tDiv = coll[i].querySelector(".program-title");
          if (overflows(tDiv))
            coll[i].classList.add("overflow");
          else // should never be executed
            coll[i].classList.remove("overflow");
        }
        var box = channel.channelDiv.getBoundingClientRect();
        this.channelsDiv.scrollLeft = box.x + (box.width - this.channelsDiv.clientWidth) * this.scrollRatio - parseFloat(window.getComputedStyle(channel.channelDiv).marginRight);
      }
      else
      {
        var box = channel.channelDiv.getBoundingClientRect();
        this.scrollRatio = box.x / (this.channelsDiv.clientWidth - box.width + 2 * parseFloat(window.getComputedStyle(channel.channelDiv).marginRight));
        this.container.classList.add("detailed");
        channel.channelDiv.classList.add("selected");
        if (overflows(channel.channelDiv.querySelector(".program-title")))
          channel.channelDiv.classList.add("expoverflow");
        else
          channel.channelDiv.classList.remove("expoverflow");
        this.state = 1;
        channel.channelDiv.querySelector(".content-y").scrollTop = 0;
      }
      window.dispatchEvent(new Event("update"));
    }).bind(this);
  }

  /** Switches to the :ref:`expanded_state`. */
  expand()
  {
    this.mouseTimer = null;
    this.container.classList.add("expanded");
    // this.container.className = "expanded";
    this.state = 2;
  }

  /**
   * Changes the player volume to the given element's value.
   *
   * @param {Element} elem - The element whose value sets the new volume
   */
  updateVolume(elem)
  {
    return (() =>
    {
      this.volume = elem.value;
      this.shadow.querySelector("video").volume = elem.value / 100;
      this.shadow.getElementById("volume1").classList.add("hidden");
      this.shadow.getElementById("volume2").classList.add("hidden");
      if (elem.value > 0)
      {
          this.shadow.getElementById("volume1").classList.remove("hidden");
          if (elem.value >= 50)
              this.shadow.getElementById("volume2").classList.remove("hidden");
      }
    }).bind(this);
  }

  /** Mutes or unmutes the player cleverly. It relies on :js:attr:`previousVolume` to get the last non-null volume. */
  switchVolume()
  {
    var vol = this.shadow.getElementById('volume');
    if (this.volume > 0)
    {
      this.previousVolume = this.volume;
      vol.value = 0;
    }
    else
    {
      this.volume = this.previousVolume;
      vol.value = this.volume;
    }
    this.updateVolume(vol)();
  }

  /**
   * Plays or pauses the Dash.js player.
   *
   * @param {Element} elem - The play/pause button whose state should be changed
   */
  playPause(elem)
  {
    if (this.playing)
    {
      //this.player.pause();
      this.playing = false;
      elem.classList.add("paused");
    }
    else
    {
      //this.player.play();
      this.playing = true;
      elem.classList.remove("paused");
    }
  }

  softUpdate()
  {
    this.currentTime = Math.round((new Date()).getTime()/1000);
    var channels_length = this.channels.length;
    for (let i = 0; i < channels_length; i++)
    {
      const channel = this.channels[i];
      channel.channelDiv.querySelector(".progress").style.width = `${channel.currentProgram.start ? Math.min(100 * (this.currentTime - channel.currentProgram.start) / (channel.currentProgram.end - channel.currentProgram.start), 100) : 0}%`;
    }
    this.updateOverlay(this.currentChannel);
  }
  
  /** Updates the programs' time trackers and replaces old programs with the ones currently being broadcast. */
  update()
  {
    this.currentTime = Math.round((new Date()).getTime()/1000);
    ajaxGet(`https://tvapi.resel.fr/v0/programs?timestamp=${this.currentTime}`, (data =>
    {
      for (let i = 0; i < this.channels.length; i++)
      {
        var channel = this.channels[i];
        channel.currentProgram = data[channel['sid']] || new Program();
  
        var titleDiv = channel.channelDiv.querySelector(".program-title");
        titleDiv.innerHTML = channel.currentProgram.title || "Indisponible";
        channel.channelDiv.querySelector(".duration").innerHTML = displayDuration(channel.currentProgram.start, channel.currentProgram.end);
        channel.channelDiv.querySelector(".subtitle").innerHTML = channel.currentProgram.subtitle || "";
        let rating = channel.currentProgram.rating;
        let ratingDiv = channel.channelDiv.querySelector(".rating");
        if (rating && rating.value)
          ratingDiv.innerHTML = `<img alt="${rating.value}" src="https://resel.fr/static/images/tv/ratings/${rating.system}/${rating.value}.svg">`;
        else
          while (ratingDiv.firstChild)
            ratingDiv.removeChild(ratingDiv.lastChild);
        channel.channelDiv.querySelector(".time").innerHTML = displayRange(channel.currentProgram.start, channel.currentProgram.end);
        channel.channelDiv.querySelector(".description p").innerHTML = channel.currentProgram.description || "Description indisponible";
        channel.channelDiv.onclick = this.switchChannel(channel);
        if (overflows(titleDiv))
          channel.channelDiv.classList.add("overflow");
        else
          channel.channelDiv.classList.remove("overflow");
        channel.channelDiv.querySelector(".progress").style.width = `${channel.currentProgram.start ? Math.min(100 * (this.currentTime - channel.currentProgram.start) / (channel.currentProgram.end - channel.currentProgram.start), 100) : 0}%`;
        this.updateOverlay(this.currentChannel);
        window.dispatchEvent(new Event("update"));
      }
    }));
  }
}

customElements.define('resel-tv', ResElTV);
