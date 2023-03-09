# **youtube-video-downloader**

Bringing you the opportunity to download content from youtube, whether it is a single media or a playlist. The choice is yours; you also have the choice of choosing the format you want it as, should it be video or audio

## **Video format**

The extension is `mp4` with the video resolution of `720p` or `360p`. 720p is the first choice when downloading and if it is not available, 360p will be the second choice. As majority of the videos contain the resolution of 360p, that is the main reason 360p is one of the option of the video resolutions. 720p is included as it is second to 360p plus the quality of the video is good enough for many of the screens the users use.

## **Audio format**

The extension is `mp4` with the audio abr (average bitrate) of `128kbps`.

## **How it works**

### **What you should do**

Pass in the youtube link to the function `youtube_download` followed by the type whether you want `video` or `audio` with the video being the default.

### **What happens when you run the code**

* A new directory for video or audio downloads will be created if it doesn't exist.
* It will check if it is playlist link or not .
* If it is not a playlist it will download the media to the current working directory.
* Otherwise if it is a playlist, the next section will go into detail what happens for a playlist.

#### **Downloading a playlist**

* A new directory will be created with the title of the playlist if it doesn't exist, that is where all the media for playlist will be downloaded to.
* Looping through the playlist:
    * The index of the media in playlist will be displayed on the terminal.
    * The title of the media to be downloaded will be displayed on the terminal.
    * It will be checked if the media doesn't already exist (checks according to filename) - if it exists it moves to the next item on the list.
    * Checks if the required type is video or audio.
    * if video:
        * It will check if the resolution 720p is available for the video otherwise it will go for 360p.
    * if audio:
        * It will select the abr of 128kbps
    * The file size will be displayed on the terminal.
    * The media will proceed to download and will display a progressbar for progress.
    * Upon completion a completion message will be displayed on the terminal.
    * should anything go wrong in the steps mentioned above a failure message will be displayed on the terminal.
* When the playlist has reached its end a completion message will be displayed on the terminal.
* An audio to signal the completion of the playlist will also sound in case the user decides to run the code in the background and do other things in the meantime.

### **Examples**

#### Single Video

```
youtube_download("https://www.youtube.com/watch?v=UmljXZIypDc")
```

#### Video Playlist or Radio

```
youtube_download("https://www.youtube.com/watch?v=UmljXZIypDc&list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p")

youtube_download("https://www.youtube.com/watch?v=z4iBXscPeqo&list=RDz4iBXscPeqo&start_radio=1&rv=z4iBXscPeqo&t=0")
```

#### Single Audio

```
youtube_download("https://www.youtube.com/watch?v=UmljXZIypDc", "audio")
```

#### Audio PLaylist

```
youtube_download("https://www.youtube.com/watch?v=UmljXZIypDc&list=PL-osiE80TeTtoQCKZ03TU5fNfx2UY6U4p", "audio")
```


## More stuff that would be nice

* Downloading media from:
    * youtube music
    * youtube shorts