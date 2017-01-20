# Video Color Analyzer
<h3> A tool to visualize the change in color over time </h3>

<h5>Instructions to run:</h5>

<p>After cloning the repository, navigate to the directory in the command line, then run the following:</p>
<p>python VideoParser.py --file {path} -f or --frames {skip count}</p>

<p><b>Path</b> A path to the video file that you want to process.</p>

<p><b>Skip Count</b> <i>Optional</i>  The number of frames to skip in between sampling for the average color.  A smaller number will have more detail but will take longer to process. The default is every 24th frame.</p> 

<p>You must have FFMPEG installed to run this program.</p>


<h3>An example of The Dark Knight</h3>
![ScreenShot](http://imgur.com/a/yyvY5)
