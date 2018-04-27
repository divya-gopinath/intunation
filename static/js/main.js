var RECORDING = false;
var audio_context = new AudioContext();
var current_exercise;
var recorded_audio;
var autotuned_audio;

$( document ).ready(function() {
    console.log( "ready!" );
    recorded_audio
    $( "#record-btn" ).click(function() {
	  if (RECORDING) { 
	  	stopRecording();
	  	$(this).css('color','black'); 
	  }
	  else { 
	  	startRecording();
	  	$(this).css('color','red');
	  }
	});
	$( "#autotune-btn" ).click(function() { 
		getAutotune();
		//if (autotuned_audio) { autotuned_audio.play(); }
		//else if (recorded_audio) { getAutotune(); }
	});
	$( "#playback-btn" ).click(function() { 
		if (recorded_audio) { recorded_audio.play(); }
	});
});

/**
 * Starts the recording process by requesting the access to the microphone.
 * Then, if granted proceed to initialize the library and store the stream.
 *
 * It only stops when the method stopRecording is triggered.
 */
function startRecording() {
	console.log("STARTING")
	RECORDING = true;
	autotuned_audio = null;
    // Access the Microphone using the navigator.getUserMedia method to obtain a stream
    navigator.getUserMedia({ audio: true }, function (stream) {
        // Expose the stream to be accessible globally
        audio_stream = stream;
        // Create the MediaStreamSource for the Recorder library
        var input = audio_context.createMediaStreamSource(stream);
        console.log('Media stream succesfully created');

        // Initialize the Recorder Library
        recorder = new Recorder(input);
        console.log('Recorder initialised');

        // Start recording !
        recorder && recorder.record();
        console.log('Recording...');

    }, function (e) {
        console.error('No live audio input: ' + e);
    });
}

/**
 * Stops the recording process. The method expects a callback as first
 * argument (function) executed once the AudioBlob is generated and it
 * receives the same Blob as first argument. The second argument is
 * optional and specifies the format to export the blob either wav or mp3
 */
function stopRecording() {
	RECORDING = false;
    // Stop the recorder instance
    recorder && recorder.stop();
    console.log('Stopped recording.');

    // Stop the getUserMedia Audio Stream !
    audio_stream.getAudioTracks()[0].stop();
    recorder && recorder.exportWAV(function (blob) {
            var audioUrl = URL.createObjectURL(blob);
            recorded_audio = new Audio(audioUrl);
            recorded_audio.crossOrigin="anonymous";
            sendRecording(blob);
            recorder.clear();
        }, "audio/wav");
}

/**
Sends recording with an AudioBlob file attachment.
POST request received by Flask and handled internally server-side.
*/
sendRecording = function(blob) {
	var formData = new FormData()
    formData.append('file', blob, 'audio') 
    formData.append('title', 'lol');
	$.ajax({
	  type: "POST",
	  url: "/save_recording",
	  data: formData,
	  processData: false,
	  contentType: false, 
	  cache: false
	});            
}

function getAutotune() { 
	$.ajax({
	  type: "GET",
	  url: "/score_recording",
	  data: "", // TODO: Change based on exercise
	}).done(function(data) {
		var reader = new FileReader();
		var blobData = new Blob([data], { type: 'audio/wav' });
		dataUrl = URL.createObjectURL(blobData);
		autotuned_audio = new Audio("http://127.0.0.1:5000/score_recording");
		autotuned_audio.crossOrigin="anonymous";
		autotuned_audio.play();
	});
}





