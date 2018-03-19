var state = 0;
var interacting = 0;

function switchChannel(sid)
{
	return function()
	{
		document.body.classList.remove("expanded");
		document.querySelector(".active").classList.remove("active");
		document.querySelector(`[data-sid="${sid}"]`).classList.remove("selected");
		document.querySelector(`[data-sid="${sid}"]`).classList.add("active");
		state = 0;
		player.attachSource(`http://172.22.199.18:9000/play/dash/${sid}/index.mpd`);
		updateOverlay(document.querySelector(`[data-sid="${sid}"]`));
	}
}

function displayDuration(start, stop)
{
	if(!stop)
	    return "Indisponible";
    var hours = Math.floor((stop - start) / 3600);
    var minutes = Math.floor((stop - start) / 60) % 60;
    var str = "";
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

function displayTime(time)
{
	date = new Date(time * 1000);
    var hours = date.getHours();
    var minutes = date.getMinutes();
    var str = "";
    if (hours < 10)
        str += '0';
    str += `${hours}:`;
    if (minutes < 10)
        str += '0';
    return str + minutes;
}

function displayRange(start, stop)
{
	if (stop)
		return `De ${displayTime(start)} à ${displayTime(stop)}`;
	else
		return "Durée indéterminée";
}

function ajaxGet(url, callback) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            try {
                var data = JSON.parse(xmlhttp.responseText);
            } catch(err) {
                console.log(err.message + " in " + xmlhttp.responseText);
                return;
            }
            callback(data);
        }
    };
 
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function updateOverlay(channel)
{
	document.getElementById("overlay-title").innerHTML = channel.querySelector(".program-title").innerHTML;
	document.getElementById("overlay-subtitle").innerHTML = channel.querySelector(".subtitle").innerHTML;
	document.getElementById("overlay-description").innerHTML = channel.querySelector(".description").innerHTML;
	document.getElementById("overlay-time").innerHTML = channel.querySelector(".time").innerHTML;
	document.getElementById("overlay-progress").style.width = channel.querySelector(".progress").style.width;
}

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

function updateVolume(value)
{
	document.querySelector("video").volume = value / 100;
	document.getElementById("volume1").classList.add("hidden");
	document.getElementById("volume2").classList.add("hidden");
	if (value > 0)
	{
		document.getElementById("volume1").classList.remove("hidden");
		if (value >= 50)
			document.getElementById("volume2").classList.remove("hidden");
	}
}

function switchVolume()
{
	var vol = document.getElementById('volume');
	if (vol.value > 0)
	{
		vol.dataset.prev = vol.value;
		vol.value = 0;
		updateVolume(0);
	}
	else
	{
		vol.value = vol.dataset.prev;
		updateVolume(vol.dataset.prev);
	}
}

function playPause(elem)
{
	if (elem.id == "stop")
	{
		player.pause();
		elem.id = "resume";
	}
	else
	{
		player.play();
		elem.id = "stop";
	}
}

var body = document.body;

function fullScreen()
{
    elem = body || document.documentElement;
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

function expand(index)
{
	return function(e)
	{
		e.stopPropagation();
		var channelDiv = document.getElementById(index.toString());
		if(channelDiv.classList.contains("selected"))
		{
			document.body.classList.remove("expanded");
			channelDiv.querySelector(".channel-more").style.visibility = "hidden";
			setTimeout(function(){channelDiv.querySelector(".channel-more").style.visibility = ""}, 200);
			channelDiv.classList.remove("selected");
			state = 0;
		}
		else
		{
			document.body.classList.add("expanded");
			channelDiv.classList.add("selected");
			titleDiv = channelDiv.querySelector(".program-title");
			if (titleDiv.scrollWidth > titleDiv.offsetWidth)
		    	channelDiv.classList.add("expoverflow");
			else
		    	channelDiv.classList.remove("expoverflow");
			state = 1;
		}
	}
}
