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
 * @param {Number} stop - The final timestamp
 * @param {Boolean} col - Whether the duration should be formatted with a colon (``hh``:``mm``)
 *                        or not (``hours`` h ``minutes`` min)
 * @returns {String} Formatted duration
 */
function displayDuration(start, stop, col)
{
    if(!start || !stop)
        return "Indisponible";
    var hours = Math.floor((stop - start) / 3600);
    var minutes = Math.floor((stop - start) / 60) % 60;
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
function displayRange(start, stop)
{
    if (stop)
        return `De ${displayTime(start)} à ${displayTime(stop)}`;
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

/*
function keyDown(e)
{
    if (!e) e=window.event;
    if (e.keyCode == 37 || e.keyCode == 39)
    {
        e.preventDefault();
        if (e.keyCode == 37)
            var newChannel = clickableChannels[(clickableChannels.indexOf(document.activeElement) + clickableChannels.length - 1) % clickableChannels.length];
        else if (e.keyCode == 39)
            var newChannel = clickableChannels[(clickableChannels.indexOf(document.activeElement) + 1) % clickableChannels.length];
            
        var startX = document.getElementsByClassName("ss-content")[0].scrollLeft;
        console.log(startX);
        var stopX = 183 * channels.indexOf(newChannel) + (183 - document.getElementById("channels").clientWidth) / 2;
        console.log(stopX);
        var step = (stopX - startX) / 10;
        var scroll = function(i){if(i == 11) return;document.getElementsByClassName("ss-content")[0].scrollLeft = startX + i * step; setTimeout(function(){scroll(i+1)}, 10);};
        scroll(1);
        newChannel.focus();
    }
}
*/

var body = document.body;

/**
 * Enters or leaves the fullscreen mode.
 */
function fullScreen()
{
    var elem = body || document.documentElement;
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
    }
}

/**
 * Class defining a TV program.
 *
 * @param {String} title - The program title
 * @param {String} subtitle - The program subtitle
 * @param {Number} start - The beginning timestamp
 * @param {Number} stop - The end timestamp
 * @param {String} desc - The program description
 */
function Program(title, subtitle, start, stop, desc)
{
    this.title = title;
    this.subtitle = subtitle;
    this.start = start;
    this.stop = stop;
    this.desc = desc;
}

/**
 * Class defining a TV channel.
 *
 * @param {Number} lcn - The logical channel number
 * @param {Number} sid - The MuMuDVB channel identifier
 * @param {Program[]} programs - The channel programs
 */
function Channel(lcn, sid, programs)
{
    this.lcn = lcn;
    this.sid = sid;
    this.programs = programs;
}

/**
 * Class defining a ResEl TV Player. It requires the document to contain
 * the main HTML elements shown in :ref:`html_design`.
 *
 * @param {Object} d - The document in which the player should lie
 * @param {Object} w - The window in which the player should lie
 * @param {String} imagePath - The location of the channels thumbnails
 */
function ResElTV(d, w, imagePath)
{
    var tv = this;
    tv.d = d;
    tv.w = w;
    tv.loadingDiv = d.getElementById("loading");
    tv.videoDiv = d.getElementById("video");
    tv.channelsDiv = d.getElementById("channels");
	
    /** Whether the client cursor is on an :ref:`Interactive Zone <interactive_zones>` or not. */
    tv.interacting = 0;
	
    /** The interface state. ``0`` is to the Normal State, ``1`` is the Expanded State and ``2`` is the Fullscreen State. See :ref:`states` for further details. */
    tv.state = 0;
	
    /** Timer until the :js:func:`fullscreen` function gets called. */
    tv.mouseTimer = null;
	
    tv.cursorVisible = true; // TODO: implement or remove

    /** The player channels list. */
    tv.channels = [];


    /** The player volume. */
    tv.volume = 100;

    /** The previous player volume. */
    tv.previousVolume = 100;

    /** Whether the player is playing or paused. */
    tv.playing = true;
	
    /** Whether the player has been fully initialized. */
    tv.init = false;
	
    tv.imagePath = imagePath;
    
    /** The Dash.js video player. */
    tv.player = dashjs.MediaPlayer().create();
    tv.player.initialize(tv.videoDiv.querySelector("video"));

    /**
     * Updates the overlay with data regarding the given channel.
     *
     * @param {Channel} channel - The channel to load the data from
     */
    tv.updateOverlay = channel => {
        var overlayTitle = tv.d.getElementById("overlay-title");
        overlayTitle.innerHTML = channel.channelDiv.querySelector(".program-title").innerHTML;
        tv.d.getElementById("overlay-subtitle").innerHTML = channel.channelDiv.querySelector(".subtitle").innerHTML;
        tv.d.getElementById("overlay-description").innerHTML = channel.channelDiv.querySelector(".description p").innerHTML;
        tv.d.getElementById("overlay-time").innerHTML = channel.channelDiv.querySelector(".time").innerHTML;
        tv.d.getElementById("overlay-progress").style.width = channel.channelDiv.querySelector(".progress").style.width;
        tv.d.getElementById("duration-indicator").innerHTML = `${displayDuration(channel.currentProgram.start, tv.currentTime, true)} / ${displayDuration(channel.currentProgram.start, channel.currentProgram.stop, true)}`;
        if (overflows(overlayTitle))
            overlayTitle.classList.add("overflow");
        else
            overlayTitle.classList.remove("overflow");
    };

    /**
     * Switches to another channel.
     *
     * @param {Channel} channel - The channel to switch to
     */
    tv.switchChannel = channel => () => {
        tv.d.body.classList.remove("expanded");
        if (tv.init)
            tv.currentChannel.channelDiv.classList.remove("active");
        channel.channelDiv.classList.remove("selected");
        channel.channelDiv.classList.add("active");
        tv.currentChannel = channel;
        if (tv.state)
        {
            var box = channel.channelDiv.getBoundingClientRect();
            tv.channelsDiv.scrollLeft = box.x + (box.width - tv.channelsDiv.clientWidth) * tv.scrollRatio - parseFloat(tv.w.getComputedStyle(channel.channelDiv).marginRight);
        }
        tv.state = 0;
        tv.player.attachSource(`https://tnt.resel.fr/play/dash/${channel.sid}/index.mpd`);
        if (tv.init)
            tv.updateOverlay(channel);
        tv.w.dispatchEvent(new Event("update"));
    };
    
    /**
     * Switches between :ref:`normal_state` and :ref:`expanded_state`.
     *
     * @param {Channel} channel - The channel whose details should be shown or hidden
     */
    tv.expand = channel => e => {
        e.stopPropagation();
        if(tv.state)
        {
            tv.d.body.classList.remove("expanded");
            channel.channelDiv.querySelector(".channel-more").style.visibility = "hidden";
            setTimeout(() => {channel.channelDiv.querySelector(".channel-more").style.visibility = ""}, 200);
            channel.channelDiv.classList.remove("selected");
            tv.state = 0;
            var coll = tv.channelsDiv.children;
            for (let i = 0; i < coll.length; i++)
            {
                var tDiv = coll[i].querySelector(".program-title");
                if (overflows(tDiv))
                    coll[i].classList.add("overflow");
                else // should never be executed
                    coll[i].classList.remove("overflow");
            }
            var box = channel.channelDiv.getBoundingClientRect();
            tv.channelsDiv.scrollLeft = box.x + (box.width - tv.channelsDiv.clientWidth) * tv.scrollRatio - parseFloat(tv.w.getComputedStyle(channel.channelDiv).marginRight);
        }
        else
        {
            var box = channel.channelDiv.getBoundingClientRect();
            tv.scrollRatio = box.x / (tv.channelsDiv.clientWidth - box.width + 2 * parseFloat(tv.w.getComputedStyle(channel.channelDiv).marginRight));
            tv.d.body.classList.add("expanded");
            channel.channelDiv.classList.add("selected");
            if (overflows(channel.channelDiv.querySelector(".program-title")))
                channel.channelDiv.classList.add("expoverflow");
            else
                channel.channelDiv.classList.remove("expoverflow");
            tv.state = 1;
            channel.channelDiv.querySelector(".content-y").scrollTop = 0;
        }
        tv.w.dispatchEvent(new Event("update"));
    };

    /** Switches to the :ref:`fullscreen_state`. */
    tv.fullscreen = () => {
        tv.mouseTimer = null;
        tv.d.body.className = "fullscreen";
        tv.state = 2;
    };

    /**
     * Changes the player volume to the given element's value.
     *
     * @param {Element} elem - The element whose value sets the new volume
     */
    tv.updateVolume = elem => () => {
        tv.volume = elem.value;
        tv.d.querySelector("video").volume = elem.value / 100;
        tv.d.getElementById("volume1").classList.add("hidden");
        tv.d.getElementById("volume2").classList.add("hidden");
        if (elem.value > 0)
        {
            tv.d.getElementById("volume1").classList.remove("hidden");
            if (elem.value >= 50)
                tv.d.getElementById("volume2").classList.remove("hidden");
        }
    };

    /** Mutes or unmutes the player cleverly. It relies on :js:attr:`previousVolume` to get the last non-null volume. */
    tv.switchVolume = () => {
        var vol = tv.d.getElementById('volume');
        if (tv.volume > 0)
        {
            tv.previousVolume = tv.volume;
            vol.value = 0;
        }
        else
        {
            tv.volume = tv.previousVolume;
            vol.value = tv.volume;
        }
        tv.updateVolume(vol)();
    };

    /**
     * Plays or pauses the Dash.js player.
     *
     * @param {Element} elem - The play/pause button whose state should be changed
     */
    tv.playPause = elem => {
        if (tv.playing)
        {
            tv.player.pause();
            tv.playing = false;
            elem.classList.add("paused");
        }
        else
        {
            tv.player.play();
            tv.playing = true;
            elem.classList.remove("paused");
        }
    };

    /** Updates the programs' time trackers and replaces old programs with the ones currently being broadcast. */
    tv.update = () => {
        tv.currentTime = Math.round((new Date).getTime()/1000);
        var channels_length = tv.channels.length;
        for (let i = 0; i < channels_length; i++)
        {
            var channel = tv.channels[i];
            if (!channel.currentProgram || tv.currentTime >= channel.currentProgram.stop)
            {
                var programs_length = channel.programs.length;
                for (let j = 0; j < programs_length; j++)
                {
                    var program = channel.programs[j];
                    if (program.start <= tv.currentTime && tv.currentTime < program.stop)
                    {
                        channel.currentProgram = program;
                        break;
                    }
                }
                if (!channel.currentProgram)
                    channel.currentProgram = new Program();

                var titleDiv = channel.channelDiv.querySelector(".program-title");
                titleDiv.innerHTML = channel.currentProgram.title || "Indisponible";
                channel.channelDiv.querySelector(".duration").innerHTML = displayDuration(channel.currentProgram.start, channel.currentProgram.stop);
                channel.channelDiv.querySelector(".subtitle").innerHTML = channel.currentProgram.subtitle || "Indisponible";
                channel.channelDiv.querySelector(".time").innerHTML = displayRange(channel.currentProgram.start, channel.currentProgram.stop);
                channel.channelDiv.querySelector(".description p").innerHTML = channel.currentProgram.desc || "Indisponible";
                channel.channelDiv.onclick = tv.switchChannel(channel);
                if (overflows(titleDiv))
                    channel.channelDiv.classList.add("overflow");
                else
                    channel.channelDiv.classList.remove("overflow");
            }
            channel.channelDiv.querySelector(".progress").style.width = `${channel.currentProgram.start ? Math.round(100 * (tv.currentTime - channel.currentProgram.start) / (channel.currentProgram.stop - channel.currentProgram.start)) : 0}%`;
            tv.updateOverlay(tv.currentChannel);
            tv.w.dispatchEvent(new Event("update"));
        }
    };

    ajaxGet('https://tnt.resel.fr/data.json', data => {
        ScrollBarX.initEl(tv.channelsDiv);
        tv.channelsDiv = tv.channelsDiv.firstChild.firstChild;

        for (var lcn in data)
        {
            var channel = new Channel(lcn, data[lcn]["sid"], data[lcn]["programs"]);
            
            tv.channelsDiv.insertAdjacentHTML('beforeend', `<div tabindex="0" class="channel" data-lcn="${lcn}"><div class="flip"><div class="card"><div class="channel-logo" style="background-image: url('${tv.imagePath}${channel.sid}.png');"></div><div class="channel-more"><div class="more-button"></div></div></div></div><div class="program"><div class="program-title"></div><div class="progressbar"><div class="progress"></div></div><div class="duration"></div></div><div class="middle"><div class="subtitle"></div><div class="time"></div></div><div class="right"><div class="description"><p></p></div></div></div>`);
            channel.channelDiv = tv.channelsDiv.lastChild;
            channel.channelDiv.onclick = tv.switchChannel(channel);
            channel.channelDiv.querySelector(".description").onclick = e => {e.stopPropagation()};
            channel.channelDiv.querySelector(".channel-more").onclick = tv.expand(channel);
            ScrollBarY.initEl(channel.channelDiv.querySelector(".description"));
            
            tv.channels.push(channel);
        }
        
        tv.switchChannel(tv.channels[0])();
        tv.init = true;
        tv.update();

        tv.channelsDiv.onmouseover = () => {
            tv.interacting = 1;
        };

        tv.channelsDiv.onmouseout = () => {
            tv.interacting = 0;
        };

        tv.d.getElementById('videobar').onmouseover = () => {
            tv.interacting = 1;
        };

        tv.d.getElementById('videobar').onmouseout = () => {
            tv.interacting = 0;
        };

        var timer = () => {
            if (tv.mouseTimer)
            {
                tv.w.clearTimeout(tv.mouseTimer);
            }
                
            if (tv.state == 2)
            {
                tv.d.body.className = "";
                tv.state = 0;
            }
        
            if (tv.state + tv.interacting == 0)
                tv.mouseTimer = tv.w.setTimeout(tv.fullscreen, 2500);
        };
    
        tv.d.onmousemove = timer;
        tv.d.onmouseup = timer;
        tv.d.onmousedown = timer;

        var playPauseButton = tv.d.getElementById("play-pause");
        playPauseButton.onclick = () => {tv.playPause(playPauseButton)};
        var volumeSlider = tv.d.getElementById("volume");
        volumeSlider.oninput = tv.updateVolume(volumeSlider);
        volumeSlider.onchange = tv.updateVolume(volumeSlider);
        volumeSlider.onmousedown = () => {if (volumeSlider.value > 0) tv.previousVolume = volumeSlider.value};
        tv.d.getElementById("sound").onclick = () => {tv.switchVolume()};
        tv.d.getElementById("fullscreen").onclick = () => {fullScreen()};
    
    
        tv.loadingDiv.classList.add("done");
        setTimeout(() => {
            tv.d.body.removeChild(tv.loadingDiv)
        }, 1000);

        setInterval(tv.update, 10000);
    });
}
