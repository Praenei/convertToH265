
if it doesn't work, update :  yt-dlp -U

yt-dlp.exe --extract-audio https://www.youtube.com/watch?v=jQ-vz2abj_g --audio-format mp3

yt-dlp.exe  https://www.youtube.com/watch?v=jQ-vz2abj_g

yt-dlp.exe https://www.youtube.com/watch?v=1_atp_n6RQM --cookies-from-browser chrome

********************************************

BBC iPlayer Downloader

This downloads either a series or a one off film/episode (depending upon the starting url) from BBC iPlayer & optionally names the file as required & adds the Season/Episode details.  All files are then converted to x265 format to save space. For non-first seasons make sure to provide the required season's url

        Examples:
        python bbci.py --url https://www.bbc.co.uk/iplayer/episodes/b03bxtqk/dragons --no-headless
        python bbci.py --url https://www.bbc.co.uk/iplayer/episodes/b03bxtqk/dragons --name "How To Train Your Dragon" --season 1 --no-headless
        python bbci.py --url https://www.bbc.co.uk/iplayer/episode/b069gxz7/bletchley-park-codebreakings-forgotten-genius
		
********************************************

Find & Convert files to H265

Run without --convert tag to just produce a csv containing all non-h265 MKV files in supplied folder & sub-folders.

	e.g.
	python findNonH265.py "F:\TV Series New"

Run with --convert to convert all non-h265 MKV files to h265 MKV files (max resolution 1080p)

	e.g. 
	python findNonH265.py "F:\TV Series New\" --convert

Only processes MKV as MP4 can struggle with converting embedded subtitles
