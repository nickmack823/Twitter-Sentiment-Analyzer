/* jshint esversion: 6 */

const durationTextObject = document.getElementById('duration-text');
const hashtagObject = document.getElementById('hashtag');
const startDateObject = document.getElementById('start-date');
const endDateObject = document.getElementById('end-date');

let avgDayScrapeTime = 50; //40 seconds/day avg
let today = new Date();
let currentMonth = (today.getMonth() + 1).toString();
let currentDay = (today.getDate()).toString();
let currentYear = (today.getFullYear()).toString();

const analyzerProgess = document.getElementById("analyzer-progress");
const progressBarAnalyzer = document.getElementById("progress-bar-analyzer");
let currentProgress = 0;


function estimateDuration() {
  let selectedStartDate = startDateObject.value;
  let selectedEndDate = endDateObject.value;
  let d1 = new Date(selectedStartDate);
  let d2 = new Date(selectedEndDate);
  let timeDiff = d2.getTime() - d1.getTime();
  let dayDiff = timeDiff / (1000 * 3600 * 24);
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

  if (startDay === currentDay && startMonth === currentMonth && startYear === currentYear) {
    window.alert('Cannot collect data starting from today, enter new start date.');
    return false;
  }
  if (parseInt(startYear) < 2008) {
    window.alert('Cannot collect data before 2008, enter new start date.');
    return false;
  }

  let endYear = input[2].slice(0, 4);
  let endDay = input[2].slice(5, 7);
  let endMonth = input[2].slice(8, 10);
  let toTheFuture = false;

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
  }
}

function advanceProgressBar() {
  // let id = setInterval(frame, 100);
  if (currentProgress < 100) {
    currentProgress++;
    progressBarAnalyzer.style.width = currentProgress + "%";
    progressBarAnalyzer.innerHTML = currentProgress + "%";
  }
}
