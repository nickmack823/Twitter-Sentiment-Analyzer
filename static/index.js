/* jshint esversion: 6 */

function toggleButton(button, mode) {
  if (mode === "on") {
    button.disabled = false;
    button.style.backgroundColor = ''; // Resets button color to keep hover functionality
  } else if (mode === "off") {
    button.disabled = true;
    button.style.backgroundColor = "gray";
  }
}

// Topic Sentiment Analyzer

const durationTextObject = document.getElementById('duration-text');
durationTextObject.style.display = "none";
const hashtagObject = document.getElementById('hashtag');
const startDateObject = document.getElementById('start-date');
const endDateObject = document.getElementById('end-date');
const dataCollectionButton = document.getElementById('data-collection-button');

let avgDayScrapeTime = 50; //40 seconds/day avg
let today = new Date();
let currentMonth = (today.getMonth() + 1).toString();
let currentDay = (today.getDate()).toString();
let currentYear = (today.getFullYear()).toString();

// Set max dates to today
startDateObject.max = today.toLocaleDateString('en-ca');
endDateObject.max = today.toLocaleDateString('en-ca');

const analyzerProgess = document.getElementById("analyzer-progress");
const progressBarAnalyzer = document.getElementById("progress-bar-analyzer");
const progressText = document.getElementById("progress-text");
let currentProgress = 0;
let daysToComplete = 0;
let progressInterval = null;
let clockInterval = null;

function secondsToHoursMinutes(value) {
    let hours = Math.floor(value / 3600);
    let minutes = Math.floor((value - (hours * 3600)) / 60);
    let seconds = value - (hours * 3600) - (minutes * 60);
    let hoursString = "hours";
    let minutesString = "minutes";
    let secondsString = "seconds";
    if (hours < 10 && hours != 0) {
      hours = "0" + hours;
      if (hours == 1) {
        hoursString = "hour";
      }
    }
    if (minutes < 10 && minutes != 0) {
      minutes = "0" + minutes;
      if (minutes == 1) {
        minutesString = "minute";
      }
    }
    if (seconds < 10) {
      seconds = "0" + seconds;
      if (seconds == 1) {
        secondsString = "second";
      }
    }
    return hours + ` ${hoursString}, ` + minutes + ` ${minutesString}, ` + seconds + ` ${secondsString}`;
}

function clockStart() {
  durationTextObject.style.display = "block";
  let secondsPassed = 0;
  return setInterval(function() { // Return interval to clear it later
    secondsPassed += 1;
    durationTextObject.innerHTML = "Time Elapsed: " + secondsToHoursMinutes(secondsPassed);
  }, 1000);
}

function inputValid(input) {
  if (input[0].includes("#")) {
    window.alert("Please remove the '#' symbol from your hashtag input.");
    return false;
  }
  if (input[0] === '' || input[1] === '' || input[2] === '') {
    window.alert('Please fill out all fields for sentiment analyzer.');
    return false;
  }
  if (/\s/.test(input[0])) { // hashtag has whitespace
    window.alert('Please remove spaces from hashtag input.');
    return false;
  }

  let startYear = input[1].slice(0, 4);
  let startMonth = input[1].slice(5, 7);
  let startDay = input[1].slice(8, 10);
  if (currentDay.length == 1) {
    currentDay = '0' + currentDay;
  }
  if (currentMonth.length == 1) {
    currentMonth = '0' + currentMonth;
  }

  // Check if start date is today
  if (startDay === currentDay && startMonth === currentMonth && startYear === currentYear) {
    window.alert('Cannot collect data starting from today, enter new start date.');
    return false;
  }

  // Check if start date before earliest available tweets
  if (parseInt(startYear) < 2008) {
    window.alert('Cannot collect data before 2008, enter new start date.');
    return false;
  }

  let endYear = input[2].slice(0, 4);
  let endMonth = input[2].slice(5, 7);
  let endDay = input[2].slice(8, 10);
  let toTheFuture = false;

  // Check if end date is in the future
  if (endYear > parseInt(currentYear)) {
    toTheFuture = true;
  } else if (endYear == parseInt(currentYear) && endMonth > parseInt(currentMonth)) {
    toTheFuture = true;
  } else if (endYear == parseInt(currentYear) && endMonth == parseInt(currentMonth) && endDay > parseInt(currentDay)) {
    toTheFuture = true;
  } else {
    toTheFuture = false;
  }

  // If trying to collect tweets from the future
  if (toTheFuture) {
    window.alert('Cannot collect data from the future, enter new end date.');
    return false;
  }

  // Check if end date is before start date
  backwards = false;
  if (endYear < startYear) {
    backwards = true;
  } else if (endYear == startYear && endMonth < startMonth) {
    backwards = true;
  } else if (endYear == startYear && endMonth == startMonth && endDay < startDay) {
    backwards = true;
  } else {
    backwards = false;
  }

  if (backwards) {
    window.alert('Start date is after end date, please input valid range.');
    return false;
  }

  // Input valid, return true
  return true;
}


function beginDataCollection() {
  let hashtag = hashtagObject.value;
  let startDate = startDateObject.value;
  let endDate = endDateObject.value;
  let input = [hashtag, startDate, endDate];
  if (inputValid(input)) {

    toggleButton(dataCollectionButton, "off");

    let selectedStartDate = startDateObject.value;
    let selectedEndDate = endDateObject.value;
    let d1 = new Date(selectedStartDate);
    let d2 = new Date(selectedEndDate);
    let timeDiff = d2.getTime() - d1.getTime();
    let dayDiff = timeDiff / (1000 * 3600 * 24);

    daysToComplete = dayDiff;
    currentProgress = 0;

    analyzerProgess.style.display = "block";
    progressBarAnalyzer.style.width = "0%";
    progressText.style.display = "block";
    progressText.style.color = "black";
    progressText.innerHTML = "0/" + daysToComplete + " Collections Completed";

    progressInterval = setInterval(updateProgress, 20000);
    clockInterval = clockStart();

    setTimeout(requestDataCollection(input), 2000);
  }
}

function requestDataCollection(input) {
  const request = new XMLHttpRequest();
  let response;
  request.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        response = this.responseText;
        // If scraper runs into an error, restart it
        if (response === "failure") {
          console.log("RECEIVE: FAILURE")
          setTimeout(requestDataCollection(input), 3000);
        } else if (response === "success") {
          // Request data for next day
          console.log("RECEIVE: SUCCESS")
          setTimeout(requestDataCollection(input), 3000);
        } else if (response === "success_end") {
            console.log("RECEIVE: SUCCESS_END")
          finishDataCollection();
        }
    }
  };
  request.open('POST', '/data-analysis', true);
  request.setRequestHeader("Content-Type", "application/json");
  request.send(JSON.stringify({hashtag: input[0], start: input[1], end: input[2]}));
}


function advanceProgressBar(progress) {
  let percentComplete = (progress/daysToComplete)*100;
  progressBarAnalyzer.style.width = percentComplete + "%";
  progressText.innerHTML = progress + "/" + daysToComplete + " Collections Completed";

  if (progress === daysToComplete) {
    finishDataCollection();
  }
}

function finalizeProgressBar() {
  analyzerProgess.style.display = "none";
  progressText.innerHTML = "Collection finished, see 'Data Viewer' for results.";
  progressText.style.color = "green";
}

function updateProgress() { // make ajax request on btn click
  $.ajax({
    type: "POST",
    url: "/update-progress", // url to the function
    success: function (daysCompleted) {
      currentProgress = daysCompleted;
      // Register new hashtag option for Data Viewer
      if (daysCompleted === 1) {
          populateDataList();
      }
      advanceProgressBar(daysCompleted); // response contains the json
    },
  });
}

function finishDataCollection() {
  finalizeProgressBar();
  clearInterval(progressInterval);
  clearInterval(clockInterval);
  toggleButton(dataCollectionButton, "on");
  const request = new XMLHttpRequest();
  request.open('POST', '/reset-progress');
  request.send();
  setTimeout(populateDataList, 5000);
}

// Single-Tweet Classifier

const tweetTextInput = document.getElementById("tweet-textinput");
const resultsTable = document.getElementById("results-table");
const classifiedTweet = document.getElementById("classified-tweet");
const classificationMajority = document.getElementById("classification-majority");

function classifyTweet() {
  let tweetInput = tweetTextInput.value;
  classifiedTweet.innerHTML = "Loading...";
  $.ajax({
    type: "POST",
    url: "/classify-tweet",
    data: tweetInput,
    success: function (classifications) {
      let pos = 0;
      let neg = 0;
      for (const [key, value] of Object.entries(classifications)) {
        if (value === "pos") {
          document.getElementById(key).innerHTML = "Positive";
          document.getElementById(key).style.color = "rgb(0, 255, 41)";
          pos += 1;
        } else {
          document.getElementById(key).innerHTML = "Negative";
          document.getElementById(key).style.color = "red";
          neg += 1;
        }
      }
      classifiedTweet.innerHTML = "Showing classifications for: " + "'" + tweetInput + "'";
      if (pos > neg) {
        classificationMajority.innerHTML = "Positive";
        classificationMajority.style.color = "rgb(0, 255, 41)";
      } else {
        classificationMajority.innerHTML = "Negative";
        classificationMajority.style.color = "red";
      }
    }
  });
}

// Data Viewer

const viewAllDataRadio = document.getElementById('view-all-data');
const viewMonthDataRadio = document.getElementById('view-month-data');
const viewYearDataRadio = document.getElementById('view-year-data');

const dataMonthDiv = document.getElementById('data-month-div');
const dataMonthInput = document.getElementById('data-month-input');
const dataYearInput = document.getElementById('data-year-input');
const dataYearDiv = document.getElementById('data-year-div');
const checkingDataText = document.getElementById('checking-data-text');
const viewDataButton = document.getElementById('view-data-button');
const downloadDataLink = document.getElementById('raw-data-link');
toggleButton(viewDataButton, "off");

const dataList = document.getElementById('data-list');
populateDataList();

if (currentMonth.length == 1) {
  dataMonthInput.max = currentYear + "-0" + currentMonth;
} else {
  dataMonthInput.max = currentYear + "-" + currentMonth;
}
dataYearInput.max = currentYear;

function selectDataFilter() {
  if (viewAllDataRadio.checked) {
    dataYearDiv.style.display = "none";
    dataMonthDiv.style.display = "none";
  } else if (viewMonthDataRadio.checked) {
    dataMonthDiv.style.display = "block";
    dataYearDiv.style.display = "none";
  } else if (viewYearDataRadio.checked) {
    dataYearDiv.style.display = "block";
    dataMonthDiv.style.display = "none";
  }
}

function setDataFilter() {
  let hashtag = dataList.options[dataList.selectedIndex].text;
  downloadDataLink.href = "static/data_files/" + hashtag + ".csv";
  downloadDataLink.innerHTML = "Download Raw Data (" + hashtag + ")";

  let data = [];
  if (viewMonthDataRadio.checked) {
    data = [hashtag, dataMonthInput.value];
  } else if (viewYearDataRadio.checked) {
    data = [hashtag, dataYearInput.value];
  } else if (viewAllDataRadio.checked) {
    data = [hashtag, ''];
  }
  let jsonInput = JSON.stringify({hashtag: data[0], other: data[1]});
  dataMonthInput.value = '';
  dataYearInput.value = '';
  toggleButton(viewDataButton, "off");
  checkingDataText.style.display = "block";
  checkingDataText.innerHTML = "Checking if any data for '" + data.toString() + "' is available...";

  $.ajax({
    type: "POST",
    url: "/get-plot",
    data: jsonInput,
    dataType: 'json',
    contentType: "application/json",
    success: function (dataExists) {
      if (dataExists) {
        checkingDataText.innerHTML = "Data exists, filter set.";
        toggleButton(viewDataButton, "on");
      } else {
        checkingDataText.innerHTML = "Data for input has not been collected/does not exist, please try new input or use Topic Sentiment Analyzer.";
      }
    },
  });
}

function populateDataList() {
  $.ajax({
    type: "POST",
    url: "/get-data-files", // url to the function
    success: function (fileList) {
      for (let i = 0; i < fileList.length; i++) {
          let file_path = fileList[i];
          let hashtag = file_path.slice(18).replace(".csv", "");
          if (i === 0) {
            downloadDataLink.href = "static/data_files/" + hashtag + ".csv";
            downloadDataLink.innerHTML = "Download Raw Data (" + hashtag + ")";
          }
          dataList.options[i] = new Option(hashtag, file_path);
      }
    }
  });
}
