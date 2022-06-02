
const durationTextObject = document.getElementById('duration-text');
const hashtagObject = document.getElementById('hashtag');
const startDateObject = document.getElementById('start-date');
const endDateObject = document.getElementById('end-date');

let avgDayScrapeTime = 0;
let today = new Date();
let currentMonth = (today.getMonth()+1).toString();
let currentDay = (today.getDate()).toString();
let currentYear = (today.getFullYear()).toString();

function estimateDuration() {
  let duration = 0;
}

function checkInputValidity(input) {
  // document.write(input);
  if (input[0] === '' || input[1] === '' || input[2] === '') {
    window.alert('Please fill out all fields for sentiment analyzer.');
    return false;
  }
  if (/\s/.test(input[0])) { // hashtag has whitespace
    window.alert('Please remove spaces from hashtag input.')
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
  window.alert([startYear, startDay, startMonth])
  window.alert([currentYear, currentDay, currentMonth])
  if (startDay === currentDay && startMonth === currentMonth && startYear === currentYear) {
    window.alert('Cannot collect data starting from today, enter new start date.')
    return false;
  }

  let endYear = input[2].slice(0, 4);
  let endDay = input[2].slice(5, 7);
  let endMonth = input[2].slice(8, 10);
  let toTheFuture = false

  if (endYear > parseInt(currentYear)) {
    toTheFuture = true;
  } else if (endYear == parseInt(currentYear) && endMonth > parseInt(currentMonth)) {
    toTheFuture = true;
  } else if (endYear == parseInt(currentYear) && endMonth == parseInt(currentMonth) && endDay > parseInt(currentDay)) {
    toTheFuture = true;
  } else {
    toTheFuture = false;
  }

  if (toTheFuture) {
    window.alert('Cannot collect data from the future, enter new end date.')
    return false;
  }
}

function beginDataCollection() {
  let hashtag = hashtagObject.value;
  let startDate = startDateObject.value;
  let endDate = endDateObject.value;
  let input = [hashtag, startDate, endDate];
  // checkInputValidity(input);
  // document.write(input);
  return checkInputValidity(input);
}
