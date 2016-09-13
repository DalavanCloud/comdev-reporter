// location may have appended ;yyyy for debugging purposes
 var srch = document.location.search.substr(1).split(';'); // drop ? from the search and split at semicolon
 var committee = srch[0]; // before the semi (if any)
 var baseyear = 1999;
 if (srch.length > 1) {
     baseyear = parseInt(srch[1]); // grab trailing start year
     if (isNaN(baseyear) || baseyear < 1970) {
         baseyear=1999; // ensure sensible default value
     }
 }
 document.getElementById('committee').value = committee;
 var date = new Date();
 var xdate = document.getElementById('xdate');
 var done = false;
 xdate.value = date.getFullYear() + "-" + ((date.getMonth()+1) < 10? "0"+(date.getMonth()+1) : (date.getMonth()+1)) + "-" + ((date.getDay()+1) < 10? "0"+(date.getDay()+1) : (date.getDay()+1))
 
 function validate(form) {
  var x = document.getElementById('xdate').value.split("-");
  // ensure UTC date is used!
  var nn = Date.UTC(x[0],parseInt(x[1])-1,parseInt(x[2]))/1000;
  document.getElementById('date').value = nn;
  if (isNaN(nn)) {
    alert("Please fill out the release date using YYYY-MMM-DD!")
    return false
  }
  var now = (new Date().getTime())/1000
  if (nn >= now) {
    alert("The date is in the future!")
    return false
  }
  return true
 }
 
 function Release(version, date) {
   this.version = version;
   this.date = date;
 }

 // display date as UTC so timezones west of GMT don't display previous date
 function toUTCDate(date) {
   return date.toUTCString().substring(0, 16)
 }

 function listReleaseData(json, a,b) {
  if (done) {
    return;
  }
  done = true
  var obj = document.getElementById('contents')
  var x = 0;
  obj.innerHTML += "<h3>Already registered releases:</h3>"
  var bd = new Date(baseyear,1,1);
  var basedate = bd.getTime()/1000 // value as stored in the database
  var recent = new Array();
  for (version in json) {
    if (json[version] > basedate) {
      recent.push(new Release(version, json[version]));
      x++;
    }
  }
  if (x == 0) {
    obj.innerHTML += "No releases registered yet since " + bd.toDateString() 
  } else {
    var now = new Date()
    recent.sort(function(a,b){return b.date - a.date}); // reverse sort
    for (idx in recent) {
      rel = recent[idx];
      d = new Date(rel.date*1000)
      obj.innerHTML += "- " + rel.version + ": " + toUTCDate(d)
      if (d > now){
        obj.innerHTML += " (<font color='red'>This is in the future?!</font>)"
      }
      obj.innerHTML +="<br>"
    }
  }
  document.getElementById('committee').value = committee;
 }
 