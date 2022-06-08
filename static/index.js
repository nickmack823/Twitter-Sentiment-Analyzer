/* jshint esversion: 6 */

// Topic Sentiment Analyzer

const durationTextObject = document.getElementById('duration-text');
const hashtagObject = document.getElementById('hashtag');
const startDateObject = document.getElementById('start-date');
const endDateObject = document.getElementById('end-date');

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

function estimateDuration() {
  let selectedStartDate = startDateObject.value;
  let selectedEndDate = endDateObject.value;
  let d1 = new Date(selectedStartDate);
  let d2 = new Date(selectedEndDate);
  let timeDiff = d2.getTime() - d1.getTime();
  let dayDiff = timeDiff / (1000 * 3600 * 24);
  daysToComplete = dayDiff;
  let durationEstimate = dayDiff * avgDayScrapeTime;
  if (!isNaN(durationEstimate)) {
    let d = new Date(0);
    d.setSeconds(durationEstimate); // specify value for SECONDS here
    let timeString = d.toISOString().substr(11, 8);
    durationTextObject.innerHTML = "Estimated duration: " + timeString;
  }
}

function inputValid(input) {
  // document.write(input);
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
    const request = new XMLHttpRequest();
    let jsonInput = JSON.stringify(input);
    request.open('POST', '/data-analysis/' + jsonInput);
    request.send();

    analyzerProgess.style.display = "block";
    progressBarAnalyzer.style.width = "0%";
    progressText.style.display = "block";
    progressText.style.color = "black";
    progressText.innerHTML = "0/" + daysToComplete + " Days Completed";

    progressInterval = setInterval(updateProgress, 10000);
  }
}


function advanceProgressBar(progress) {
  let percentComplete = (progress/daysToComplete)*100;
  progressBarAnalyzer.style.width = percentComplete + "%";
  progressText.innerHTML = progress + "/" + daysToComplete + " Days Completed";

  if (progress === daysToComplete) {
    finalizeProgressBar();
  }
}

function finalizeProgressBar() {
  analyzerProgess.style.display = "none";

  progressText.innerHTML = "Collection finished, see 'Data Viewer' for results.";
  progressText.style.color = "green";

  const request = new XMLHttpRequest();
  request.open('POST', '/reset-progress');
  request.send();

  clearInterval(progressInterval);
}

function updateProgress() { // make ajax request on btn click
  $.ajax({
    type: "POST",
    url: "/update-progress", // url to the function
    success: function (daysCompleted) {
      advanceProgressBar(daysCompleted); // response contains the json
    },
  });
}

// Data Viewer

const viewAllDataRadio = document.getElementById('view-all-data');
const viewMonthDataRadio = document.getElementById('view-month-data');
const viewYearDataRadio = document.getElementById('view-year-data');
let selectedFilter = 'all';

const dataMonthDiv = document.getElementById('data-month-div');
const dataMonthInput = document.getElementById('data-month-input');
const dataYearInput = document.getElementById('data-year-input');
const dataYearDiv = document.getElementById('data-year-div');
const viewDataButton = document.getElementById('view-data-button');
viewDataButton.disabled = true;
viewDataButton.style.backgroundColor = "gray";

if (currentMonth.length == 1) {
  dataMonthInput.max = currentYear + "-0" + currentMonth;
} else {
  dataMonthInput.max = currentYear + "-" + currentMonth;
}
dataYearInput.max = currentYear;

function selectDataFilter() {
  if (viewAllDataRadio.checked) {
    selectedFilter = 'all';
    dataYearDiv.style.display = "none";
    dataMonthDiv.style.display = "none";
  } else if (viewMonthDataRadio.checked) {
    selectedFilter = 'month';
    dataMonthDiv.style.display = "block";
    dataYearDiv.style.display = "none";
  } else if (viewYearDataRadio.checked) {
    selectedFilter = 'year';
    dataYearDiv.style.display = "block";
    dataMonthDiv.style.display = "none";
  }
}

function setDataFilter() {
  const request = new XMLHttpRequest();
  let hashtag = document.getElementById('data-hashtag').value;
  let data = [];
  if (selectedFilter === "month") {
    data = [hashtag, dataMonthInput.value];
  } else if (selectedFilter === "year") {
    data = [hashtag, dataYearInput.value];
  } else if (selectedFilter === "all") {
    data = [hashtag];
  }
  let jsonInput = JSON.stringify({hashtag: data[0], other: data[1]});
  request.open('POST', '/get-plot/' + jsonInput);
  request.send();
  document.getElementById('data-hashtag').value = '';
  dataMonthInput.value = '';
  dataYearInput.value = '';
  viewDataButton.style.backgroundColor = "dodgerblue";
  viewDataButton.disabled = false;
  return false;
}

// Single-Tweet Classifier

const tweetTextInput = document.getElementById("tweet-textinput");

function classifyTweet() {
  let tweetInput = tweetTextInput.value;
  let jsonInput = JSON.stringify(tweetInput);
  request.open('POST', '/classify-tweet/' + jsonInput);
  request.send();
}
