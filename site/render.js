var jsdata = {}

var templates = {}
var nproject = null;

// Function for async fetching of a single JSON file with JS callback

function GetAsyncJSON(theUrl, xstate, callback) {
	var xmlHttp = null;
	if (window.XMLHttpRequest) {
		xmlHttp = new XMLHttpRequest();
	} else {
		xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
	}
	xmlHttp.open("GET", theUrl, true);
	xmlHttp.send(null);
	xmlHttp.onprogress = function(state) {
		var s = parseInt(xmlHttp.getResponseHeader('Content-Length'))
		if (document.getElementById('pct')) {
			document.getElementById('pct').innerHTML = "<p style='text-align: center;'><b><i>Loading: " + parseInt((100 * (xmlHttp.responseText.length / s))) + "% done</i></b></p>";
		}
	}
	xmlHttp.onreadystatechange = function(state) {

		if (xmlHttp.readyState == 4 && xmlHttp.status == 200 || xmlHttp.status == 404) {
			if (callback) {
				if (xmlHttp.status == 404) {
					callback({}, xstate);
				} else {
					if (document.getElementById('pct')) {
						document.getElementById('pct').innerHTML = "<p style='text-align: center;'><b><i>Loading: 100% done</i></b></p>";
					}
					window.setTimeout(callback, 0.05, JSON.parse(xmlHttp.responseText), xstate);
				}
			}
		}
	}
}


function makeSelect(name, arr, sarr) {
	var sel = document.createElement('select');
	sel.setAttribute("name", name)
	for (i in arr) {
		var val = arr[i];
		var opt = document.createElement('option')
		opt.setAttribute("value", val)
		opt.innerHTML = val
		sel.appendChild(opt);
	}
	return sel
}

function getWednesdays(mo, y) {
	var d = new Date();
	if (mo) {
		d.setMonth(mo);
	}
	if (y) {
		d.setFullYear(y, d.getMonth(), d.getDay())
	}
	var month = d.getMonth(),
		wednesdays = [];

	d.setDate(1);

	// Get the first Monday in the month
	while (d.getDay() !== 3) {
		d.setDate(d.getDate() + 1);
	}

	// Get all the other Mondays in the month
	while (d.getMonth() === month) {
		wednesdays.push(new Date(d.getTime()));
		d.setDate(d.getDate() + 7);
	}

	return wednesdays;
}

function setReportDate(json, x) {
	var pmc = x[0]
	var reportdate = x[1]
	var fullname = (x[2] ? x[2] : "Unknown").replace(/Apache /, "")
	var m = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
	var today = new Date()

	var dates = []
	if (!json[pmc]) {
		pmc = fullname
	}
	for (i in json[pmc]) {
		tm = 0;
		sm = json[pmc][i]
		for (x in m) {
			if (m[x] == sm) {
				tm = x;
			}
		}
		dates.push(getWednesdays(tm)[2])
	}
	var ny = today.getFullYear() + 1;
	for (i in json[pmc]) {
		tm = 0;
		sm = json[pmc][i]
		for (x in m) {
			if (m[x] == sm) {
				tm = x;
			}
		}
		dates.push(getWednesdays(tm)[2], ny)
	}
	var nextdate = dates[0];
	while (nextdate < today) {
		nextdate = dates.shift();
	}
	reportdate.innerHTML += "<b>Next report date: " + (nextdate ? nextdate.toDateString() : "Unknown(?)") + "</b>"
	if (nextdate) {
		var link = "https://svn.apache.org/repos/private/foundation/board/board_agenda_" +  nextdate.getFullYear() + "_" + (nextdate.getMonth() < 9 ? "0" : "") + (nextdate.getMonth() +1) + "_" + nextdate.getDate() + ".txt"
		reportdate.innerHTML += "<br>File your report in <a href='"+link+"'>"+link+"</a> when it has been seeded."
	}
	
}

function buildPanel(pmc, title) {
	var parent = document.getElementById('tab_' + pmc);

	var toc = document.getElementById('toc_' + pmc);
	if (!toc) {
		toc = document.createElement('cl')
		toc.setAttribute("class", "sub-nav")
		toc.setAttribute("id", "toc_" + pmc)
		if (parent.firstChild.nextSibling) {
			parent.insertBefore(toc, parent.firstChild.nextSibling);
		} else {
			parent.appendChild(toc)
		}
	}
	var linkname = title.toLowerCase().replace(/[^a-z0-9]+/, "")
	var li = document.createElement('dd');
	li.setAttribute("role", "menu-item")
	li.innerHTML = "<a href='#" + linkname + "_" + pmc + "'>" + title + "</a>"
	toc.appendChild(li)

	var div = document.createElement('div');
	div.setAttribute("id", linkname + "_" + pmc);
	parent.appendChild(div)

	var titlebox = document.createElement('div');
	titlebox.innerHTML = "<h3 style='background: #666; color: #EEE; border: 1px solid #66A; margin-top: 30px;'>" + title + " &nbsp; &nbsp; <small> <b>&uarr;</b> <a href='#tab_" + pmc + "'>Back to top</a></small></h3>"
	div.appendChild(titlebox);
	return div;
}

function addLine(pmc, line) {
	line = line ? line : "  "
	var lines = line.split(/\n/)
	for (x in lines) {
		var xline = lines[x]
		var words = xline.split(" ")
		var len = 0;
		var out = ""
		for (i in words) {
			len += words[i].replace(/<.+?>/, "").length + (i == words.length - 1 ? 0 : 1)
			if (len >= 78) {
				out += "\n   "
				len = words[i].replace(/<.+?>/, "").length + (i == words.length - 1 ? 0 : 1)
			}
			out += words[i] + " "
		}
		templates[pmc] += out + "\n"
	}
}

function renderFrontPage(json) {
	jsdata = json
	var container = document.getElementById('contents')
	container.innerHTML = "<h2 style='text-align: center; margin-bottom: 10px;' class='hide-for-small-only'>Apache Committee Report Helper</h2>Click on a committee name to view statistics:"
	var top = document.createElement('div');
	container.appendChild(top)


	var panellist = document.createElement('ul');
	panellist.style.background = "#AAA"
	panellist.style.textAlign = "center"
	panellist.style.margin = "0 auto"
	panellist.style.paddingLeft = "5px"
	//panellist.setAttribute("class", "tabs")
	panellist.setAttribute("id", "tabs");
	panellist.setAttribute("data-tab", "")
	panellist.setAttribute("role", "tablist")
	container.appendChild(panellist)

	var pcontainer = document.createElement('div');
	pcontainer.setAttribute("id", "tabcontents")
	pcontainer.setAttribute("style", "text-align: left !important; margin: 0 auto; width: 1000px; border-radius: 5px; border: 2px solid #666; height: 100%; overflow: scroll !important; overflow-y: scroll !important; ")
	container.appendChild(pcontainer)

	var sproject = document.location.search.substr(1);
	var hcolors = ["#000070", "#007000", "#407000", "#70500", "#700000", "#A00000"]
	var hvalues = ["Super Healthy", "Healthy", "Mostly Okay", "Unhealthy", "Action required!", "URGENT ACTION REQUIRED!"]
	for (i in json.pmcs) {

		var pmc = json.pmcs[i]
		templates[pmc] = "Report from the " + (json.pdata[pmc].name ? json.pdata[pmc].name : pmc) + " committee [" + (json.pdata[pmc].chair ? json.pdata[pmc].chair : "Put your name here") + "]\n\n"

		addLine(pmc, "## Description:")
		if (json.pdata[pmc].shortdesc) {
			addLine(pmc, "   " + json.pdata[pmc].shortdesc)
		} else {
			addLine(pmc, " - <font color='red'>Description goes here</font>")
		}
		addLine(pmc)

		addLine(pmc, "## Activity:")
		addLine(pmc, " - <font color='red'>TODO - the PMC <b><u>MUST</u></b> provide this information</font>")
		addLine(pmc)

		addLine(pmc, "## Issues:")
		addLine(pmc, " - <font color='red'>TODO - list any issues that require board attention, \n  or say \"there are no issues requiring board attention at this time\"</font>")
		addLine(pmc)

		var obj = document.createElement('div');
		obj.setAttribute("id", "tab_" + pmc)
		obj.style = "padding: 10px; text-align: left !important;"
		obj.setAttribute("aria-hidden", "true")
		var title = document.createElement('h2')
		title.innerHTML = json.pdata[pmc].name ? json.pdata[pmc].name : pmc
		obj.appendChild(title)
		var health = document.createElement('p');
		if (json.health[pmc] && !isNaN(json.health[pmc]['cscore'])) {
			health.style.marginTop = "10px"
			health.innerHTML = "<b>Committee Health score:</b> <a href='/chi.py#"+pmc+"'><u><font color='" + hcolors[json.health[pmc]['cscore']] + "'>" + (6.33+(json.health[pmc]['score']*-1.00*(20/12.25))).toFixed(2) + " (" + hvalues[json.health[pmc]['cscore']] + ")</u></font></a>"
			obj.appendChild(health)
		}
		pcontainer.appendChild(obj)



		// Report date

		var mo = new Date().getMonth();
		var reportdate = buildPanel(pmc, "Report date")
		if (json.pdata[pmc].chair) {
			reportdate.innerHTML += "<b>Committee Chair: </b>" + json.pdata[pmc].chair + "<br>"
		}
		GetAsyncJSON("reportingcycles.json?" + Math.random(), [pmc, reportdate, json.pdata[pmc].name], setReportDate)


		// LDAP committee + Committer changes

		var mo = new Date().getMonth() - 3;
		var after = new Date();
		after.setMonth(mo);

		var changes = buildPanel(pmc, "LDAP committee group/Committership changes");

		var c = 0;
		for (i in json.changes[pmc].committer) c++;
		for (i in json.changes[pmc].pmc) c++;
		var nc = 0;
		var np = 0;
		var ncn = null;
		var npn = null;
		addLine(pmc, "## LDAP committee group/Committership changes:")
		addLine(pmc)
		addLine(pmc, " - Currently " + json.count[pmc][1] + " committers and " + json.count[pmc][0] + " LDAP committee group members.")
		if (c == 0) {
			changes.innerHTML += "<font color='red'><b>No new changes to the LDAP committee group or committer base detected - (LDAP error or no changes for &gt;2 years)</b></font>"
			addLine(pmc, " - No new changes to the LDAP committee group or committership since last report.")
			addLine(pmc)
		} else {
			changes.innerHTML += "<h5>Changes within the last 3 months:</h5>"
			var l = 0;
			
			// pre-flight check
			var npmc = 0;
			for (i in json.changes[pmc].pmc) {
				var entry = json.changes[pmc].pmc[i];
				if (entry[1] > after.getTime() / 1000) {
					npmc++;
				}
			}
			if (npmc > 1) {
				addLine(pmc, " - New LDAP committee group members:")
			}
			
			
			for (i in json.changes[pmc].pmc) {
				var entry = json.changes[pmc].pmc[i];
				if (entry[1] > np) {
					np = entry[1]
					npn = entry[0];
				}
				if (entry[1] > after.getTime() / 1000) {
					l++;
					changes.innerHTML += "&rarr; " + entry[0] + " was added to the LDAP committee group on " + new Date(entry[1] * 1000).toDateString() + "<br>";
					addLine(pmc, (npmc>1? "   " : "") + " - " + entry[0] + " was added to the LDAP committee group on " + new Date(entry[1] * 1000).toDateString())
				}
			}
			if (l == 0) {
				addLine(pmc, " - No new LDAP committee group members added in the last 3 months")
				changes.innerHTML += "&rarr; <font color='red'><b>No new LDAP committee group members in the last 3 months.</b></font><br>";
			}
			if (npn) {
				if (np < after.getTime() / 1000) {
					addLine(pmc, " - Last LDAP committee group addition was " + npn + " at " + new Date(np * 1000).toDateString())
				}
				changes.innerHTML += "&rarr; " + "<b>Latest LDAP committee group addition: </b>" + new Date(np * 1000).toDateString() + " (" + npn + ")<br>"
			}
			
			
			// pre-flight check
			var ncom = 0;
			for (i in json.changes[pmc].committer) {
				var entry = json.changes[pmc].committer[i];
				if (entry[1] > after.getTime() / 1000) {
					ncom++;
				}
			}
			if (ncom > 1) {
				addLine(pmc, " - New commmitters:")
			}
			for (i in json.changes[pmc].committer) {
				var entry = json.changes[pmc].committer[i];
				if (entry[1] > nc) {
					nc = entry[1]
					ncn = entry[0];
				}
				if (entry[1] > after.getTime() / 1000) {
					l++;
					changes.innerHTML += "&rarr; " + entry[0] + " was added as a committer on " + new Date(entry[1] * 1000).toDateString() + "<br>";
					addLine(pmc, (ncom>1? "   " : "") + " - " + entry[0] + " was added as a committer on " + new Date(entry[1] * 1000).toDateString())
				}
			}
			if (l == 0) {
				changes.innerHTML += "&rarr; <font color='red'><b>No new committers in the last 3 months.</b></font><br>";
				addLine(pmc, " - No new committers added in the last 3 months")
			}
			
			if (ncn) {
				if (nc < after.getTime() / 1000) {
					addLine(pmc, " - Last committer addition was " + ncn + " at " + new Date(nc * 1000).toDateString())
				}
				changes.innerHTML += "&rarr; " + "<b>Latest committer addition: </b>" + new Date(nc * 1000).toDateString() + " (" + ncn + ")<br>"
			} else {
				addLine(pmc, " - Last committer addition was more than 2 years ago")
				changes.innerHTML += "&rarr; " + "<b>Latest committer addition: </b><font color='red'>more than two years ago (not in the archive!)</font><br>"
			}
			changes.innerHTML += "&rarr; " + "<b>Currently " + json.count[pmc][1] + " committers and " + json.count[pmc][0] + " LDAP committee members."
			addLine(pmc)
		}

		// Release data

		var releases = buildPanel(pmc, "Releases")
		addLine(pmc, "## Releases:")
		addLine(pmc)
		var nr = 0;
		var lr = null;
		var lrn = 0;
		var tr = 0
		for (version in json.releases[pmc]) {
			tr++;
			var date = parseInt(json.releases[pmc][version])
			if (date > lrn) {
				lrn = date
				lr = version
			}
			if (date >= after.getTime() / 1000) {
				err = ""
				if (new Date(date * 1000) > new Date()) {
					err = " (<font color='red'>This seems wrong?!</font>)"
				}
				releases.innerHTML += "&rarr; " + "<b>" + version + " was released on </b>" + new Date(date * 1000).toDateString() + err + "<br>"
				addLine(pmc, " - " + version + " was released on " + new Date(date * 1000).toDateString() + err)
				nr++;
			}
		}

		if (nr == 0) {
			if (lr) {
				releases.innerHTML += "&rarr; " + "<b>Latest release was " + lr + ", released on </b>" + new Date(lrn * 1000).toDateString() + "<br>"
				addLine(pmc, " - Last release was " + lr + " on " + new Date(lrn * 1000).toDateString())
			} else {
				releases.innerHTML += "No release data could be found.<br>"
				addLine(pmc, " - <font color='red'>No release data could be found [FIX!]</font>")
			}
		}
		releases.innerHTML += "<i>(A total of " + (tr - nr) + " older release(s) were found for " + pmc + " in our db)</i><br>"
		releases.innerHTML += "<br><a href='javascript:void(0);' onclick=\"$('#rdialog_" + pmc + "').dialog({minWidth: 450, minHeight: 240});\">Add a release</a> - <a href='javascript:void(0);' onclick=\"$('#dialog_" + pmc + "').dialog({minWidth: 450, minHeight: 240});\">Fetch releases from JIRA</a>"
		releases.innerHTML += " - <a href='/addrelease.html?" + pmc + "'>Manage release versions</a><br>"

		if (tr > 0) {
			var div = renderReleaseChart(json.releases[pmc], pmc, releases);
			releases.appendChild(div)
		}


		addLine(pmc)

		var mlbox = buildPanel(pmc, "Mailing lists");

		var ul = document.createElement('ul')
		ul.style.textAlign = "left;"
		mlbox.appendChild(ul)
		var prev = ""
		var f = 0
		addLine(pmc, "## Mailing list activity:")
		addLine(pmc)
		var first = ['users', 'dev', 'commits', 'private', 'bugs', 'modules-dev'];


		for (i in first) {

			ml = pmc + ".apache.org-" + first[i]
			if (ml != prev && ml.search("infra") < 0 && json.mail[pmc] && json.mail[pmc][ml]) {
				f++;
				prev = ml
				var d = ml.split(".org-");
				var mlname = d[1] + "@" + d[0] + ".org"
				var lookup = d[0].split(/\./)[0] + "-" + d[1]

				var x = renderChart(json.mail[pmc], ml, obj, (json.delivery[pmc] && json.delivery[pmc][lookup]) ? json.delivery[pmc][lookup].weekly : {})
				var total = x[0]
				var diff = x[1]
				var div = x[2]

				add = ""
				if (json.delivery[pmc] && json.delivery[pmc][lookup]) {
					add = ":\n    - " + json.delivery[pmc][lookup].quarterly[0] + " emails sent to list (" + json.delivery[pmc][lookup].quarterly[1] + " in previous quarter)";
				}
				var text = "Currently: " + total + " subscribers <font color='green'>(up " + diff + " in the last 3 months)</font>"
				if (diff < 0) {
					text = "Currently: " + total + " subscribers <font color='red'>(down " + diff + " in the last 3 months)</font>"
					if (d[1] != "private" && d[1] != "security" && d[1] != "commits") {
						addLine(pmc, " - " + mlname + ": ")
						addLine(pmc, "    - " + total + " subscribers (down " + diff + " in the last 3 months)" + add)
						addLine(pmc)
					}
				} else {
					if (d[1] != "private" && d[1] != "security" && d[1] != "commits") {
						addLine(pmc, " - " + mlname + ": ")
						addLine(pmc, "    - " + total + " subscribers (up " + diff + " in the last 3 months)" + add)
						addLine(pmc)
					}
				}

				if (json.delivery[pmc] && json.delivery[pmc][lookup]) {
					text += " (" + json.delivery[pmc][lookup].quarterly[0] + " emails sent in the past 3 months, " + json.delivery[pmc][lookup].quarterly[1] + " in the previous cycle)"
				}

				var p = document.createElement('li');
				p.innerHTML = "<h5>" + mlname + ":</h5>" + text
				p.appendChild(div)
				ul.appendChild(p)
			}
		}

		for (ml in json.mail[pmc]) {
			var skip = false
			for (i in first) {
				xml = pmc + ".apache.org-" + first[i]
				if (ml.search(xml) == 0) {
					skip = true
				}
			}
			if (!skip) {

				f++;
				if (ml != prev && ml.search("infra") < 0) {
					prev = ml
					var d = ml.split(".org-");
					var mlname = d[1] + "@" + d[0] + ".org"
					var lookup = d[0].split(/\./)[0] + "-" + d[1]
					var x = renderChart(json.mail[pmc], ml, obj, (json.delivery[pmc] && json.delivery[pmc][lookup]) ? json.delivery[pmc][lookup].weekly : {})
					var total = x[0]
					var diff = x[1]
					var div = x[2]

					add = ""
					if (json.delivery[pmc] && json.delivery[pmc][lookup]) {
						add = ":\n    - " + json.delivery[pmc][lookup].quarterly[0] + " emails sent to list (" + json.delivery[pmc][lookup].quarterly[1] + " in previous quarter)";
					}
					var text = "Currently: " + total + " subscribers <font color='green'>(up " + diff + " in the last 3 months)</font>"
					if (diff < 0) {
						text = "Currently: " + total + " subscribers <font color='red'>(down " + diff + " in the last 3 months)</font>"
						if (d[1] != "private" && d[1] != "security" && d[1] != "commits") {
							addLine(pmc, " - " + mlname + ": ")
							addLine(pmc, "    - " + total + " subscribers (down " + diff + " in the last 3 months)" + add)
							addLine(pmc)
						}
					} else {
						if (d[1] != "private" && d[1] != "security" && d[1] != "commits") {
							addLine(pmc, " - " + mlname + ": ")
							addLine(pmc, "    - " + total + " subscribers (up " + diff + " in the last 3 months)" + add)
							addLine(pmc)
						}
					}

					if (json.delivery[pmc] && json.delivery[pmc][lookup]) {
						text += " (" + json.delivery[pmc][lookup].quarterly[0] + " emails sent in the past 3 months, " + json.delivery[pmc][lookup].quarterly[1] + " in the previous cycle)"
					}

					var p = document.createElement('li');
					p.innerHTML = "<h5>" + mlname + ":</h5>" + text
					p.appendChild(div)
					ul.appendChild(p)
				}
			}
		}
		addLine(pmc)

		// Add btn for nav
		if (f > 0) {
			var btn = document.createElement('li');
			btn.setAttribute("id", "btn_" + pmc)
			btn.setAttribute("class", "tab-title")
			btn.setAttribute("onclick", "$('#tabcontents').animate({scrollTop: -99999}, 500)");
			btn.innerHTML = "<a href='#' name='tab_" + pmc + "'>" + pmc + "</a>"
			panellist.appendChild(btn)
			if (sproject && sproject == pmc) {
				$('#btn_' + pmc).click();
				$('#' + pmc).addClass("active");
			}

		}




		if (json.jira[pmc][0] > 0 || json.jira[pmc][1] > 0) {
			renderJIRA(pmc)
		}


		// Reporting example
		var template = buildPanel(pmc, "Report template");
		template.innerHTML += "<pre style='border: 2px dotted #444; padding: 10px; background: #FFD;' contenteditable='true'>" + templates[pmc] + "</pre>"

		// Fetch from JIRA dialog
		var dialog = document.createElement('div');
		dialog.setAttribute("id", "dialog_" + pmc);
		dialog.setAttribute("title", "Fetch data from JIRA")
		dialog.setAttribute("style", "display: none;")
		dialog.innerHTML = "<form><b>JIRA Project:</b><input type='text' name='jira' placeholder='FOO'><br><b>Optional prepend:</b> <input name='prepend' type='text' placeholder='Foo'/><br><input type='button' value='Fetch from JIRA' onclick='fetchJIRA(\"" + pmc + "\", this.form[\"jira\"].value, this.form[\"prepend\"].value);'></form><p>If you have multiple JIRA projects and they only have the version number in their release versions, please enter the component name in the 'prepend' field.</p>"
		document.getElementById('tab_' + pmc).appendChild(dialog)
		
		// Manually add release dialog
		var rdialog = document.createElement('div');
		rdialog.setAttribute("id", "rdialog_" + pmc);
		rdialog.setAttribute("title", "Add a release")
		rdialog.setAttribute("style", "display: none;")
		rdialog.innerHTML = "<form><b>Version:</b><input type='text' name='version' placeholder='1.2.3'><br><b>Date:</b> <input name='date' type='text' placeholder='YYYY-MM-DD'/><br><input type='button' value='Add release' onclick='addRelease(\"" + pmc + "\", this.form[\"version\"].value, this.form[\"date\"].value);'></form>"
		document.getElementById('tab_' + pmc).appendChild(rdialog)

	}
	if (json.pmcs.length == 0) {
		container.innerHTML = "You are not a member of any PMC, sorry!"
	}

	$("#tabcontents").find("[id^='tab']").hide();



	$('#tabs a').click(function(e) {
		e.preventDefault();
		if ($(this).closest("li").attr("id") == "current") {
			return;
		} else {
			$("#tabcontents").find("[id^='tab_']").hide();
			$("#tabs li").attr("id", "");
			$(this).parent().attr("id", "current");
			$('#' + $(this).attr('name')).fadeIn();
		}
	});

	var project = nproject ? nproject : document.location.search.substr(1);

	if (project && project.length > 0) {
		$("#tabcontents #tab_" + project).fadeIn();
		$("#tabs #btn_" + project).attr('id', 'current');
	}
	if (json.all && json.all.length > 0) {
		var btn = document.createElement('li');
		btn.setAttribute("style", "margin-left: 48px;")
		btn.setAttribute("id", "btn_all")
		btn.setAttribute("class", "tab-title")
		if (json.all.indexOf("-----------------------") == -1) {
			json.all.sort()
			json.all.unshift("-----------------------")
			json.all.unshift("Members-only Quick-nav:")
		}
		
		var sel = makeSelect("project", json.all, [])
		sel.setAttribute("style", "height: 32px !important; padding: 0px !important; margin: 0px !important; margin-left: 32px !important;")
		sel.style = "break-before: never; break-after: never; float: left"
		sel.setAttribute("onchange", "GetAsyncJSON('/getjson.py?only='+ this.value, this.value, mergeData);")
		btn.appendChild(sel)
		panellist.appendChild(btn)

	}



}

function mergeData(json, pmc) {
	if (jsdata.pmcs.indexOf(pmc) >= 0) {
		return
	}
	if (nproject && nproject.length > 0) {
		for (i in jsdata.pmcs) {
			if (jsdata.pmcs[i] == nproject) {
				jsdata.pmcs.splice(i,1);
				break
			}
		}
	}
	
	var todo = new Array('count', 'mail', 'delivery', 'jira', 'changes', 'pdata', 'releases', 'keys', 'health')
	for (i in todo) {
		var key = todo[i]
		jsdata[key][pmc] = json[key][pmc];
	}
	jsdata.pmcs.push(pmc)
	nproject = pmc
	renderFrontPage(jsdata)
}


function renderJIRA(pmc) {
	var obj = buildPanel(pmc, "JIRA Statistics")

	addLine(pmc, "## JIRA activity:")
	addLine(pmc)
	addLine(pmc, " - " + jsdata.jira[pmc][0] + " JIRA tickets created in the last 3 months");
	addLine(pmc, " - " + jsdata.jira[pmc][1] + " JIRA tickets closed/resolved in the last 3 months");
	addLine(pmc)
	obj.innerHTML += jsdata.jira[pmc][0] + " JIRA tickets created in the last 3 months<br>";
	obj.innerHTML += jsdata.jira[pmc][1] + " JIRA tickets closed/resolved in the last 3 months<br>";
	if (jsdata.keys[pmc]) {
		obj.innerHTML += "Keys used: <kbd>" + jsdata.keys[pmc].join(", ") + "</kbd>"
	}

}


function renderChart(json, name, container, delivery) {

	var chartDiv = document.createElement('div')
	chartDiv.setAttribute("id", name + "_chart")
	var dates = []
	var noweekly = 0;
	for (date in json[name]) {
		dates.push(date)
	}
	for (date in delivery) noweekly++;
	var d = name.split(".org-");
	var mlname = d[1] + "@" + d[0] + ".org"
	dates.sort();
	var cu = 0;
	narr = []
	hitFirst = false

	var dp = new Date();
	dp.setMonth(dp.getMonth() - 3);

	var odp = new Date();
	odp.setMonth(odp.getMonth() - 6);

	difference = 0
	for (i in dates) {
		var date = dates[i];
		var dateString = new Date(parseInt(date) * 1000);
		if (dateString > dp) {
			difference += json[name][date]
		}
		cu = cu + json[name][date];
		if (cu > 0) {
			hitFirst = true
		}
		if ((cu > 0 || hitFirst) && dateString >= odp) {
			if (noweekly > 0) {
				narr.push([dateString, cu, delivery[date] ? delivery[date] : 0])
			} else {
				narr.push([dateString, cu])
			}
		}

	}

	var data = new google.visualization.DataTable();
	data.addColumn('date', 'Date');
	data.addColumn('number', "List members");
	if (noweekly > 0) {
		data.addColumn('number', "Emails sent per week");
	}

	data.addRows(narr);


	var options = {
		title: 'Mailing list stats for ' + mlname,
		backgroundColor: 'transparent',
		width: 900,
		height: 260,
		legend: {
			position: 'none',
			maxLines: 3
		},
		vAxis: {
			format: "#"
		},
		vAxes: (noweekly > 0) ? [

			{
				title: 'Emails per week',
				titleTextStyle: {
					color: '#DD0000'
				}
			}, {
				title: 'Subscribers',
				titleTextStyle: {
					color: '#0000DD'
				}
			},
		] : [{
				title: 'Subscribers',
				titleTextStyle: {
					color: '#0000DD'
				}
			},
		],
		series: {
			0: {
				type: "line",
				pointSize: 4,
				lineWidth: 2,
				targetAxisIndex: (noweekly > 0) ? 1 : null
			},
			1: {
				type: "bars",
				targetAxisIndex: (noweekly > 0) ? 0 : [0, 1]
			}
		},
		seriesType: "bars",
		tooltip: {
			isHtml: true
		},
	};

	var chart = new google.visualization.ComboChart(chartDiv);

	chart.draw(data, options);
	return [cu, difference, chartDiv];

}



function renderReleaseChart(releases, name, container) {


	var chartDiv;
	if (document.getElementById(name + "_releasechart")) {
		chartDiv = document.getElementById(name + "_releasechart")
	} else {
		chartDiv = document.createElement('div')
		chartDiv.setAttribute("id", name + "_releasechart")
	}

	var narr = []
	var maxLen = 1;
	for (version in releases) {
		var x = version.match(/(\d+)\.(\d+)/)
		if (x && x[2].length > maxLen) {
			maxLen = x[2].length;
		}
	}
	for (version in releases) {
		if (new Date(releases[version] * 1000).getFullYear() >= 1999) {
			var major = parseFloat(version) ? parseFloat(version) : 1
			var x = version.match(/(\d+)\.(\d+)/)
			if (x) {
				while (x[2].length < maxLen) {
					x[2] = "0" + x[2]
				}
				major = parseFloat(x[1] + "." + x[2])
			}
			narr.push([new Date(releases[version] * 1000), major, version + " - " + new Date(releases[version] * 1000).toDateString()])
		}

	}

	var data = new google.visualization.DataTable();

	data.addColumn('datetime', 'Date');
	data.addColumn('number', 'Version')
	data.addColumn('string', 'tooltip');
	data.setColumnProperty(2, 'role', 'tooltip');

	data.addRows(narr);


	var options = {
		title: 'Release timeline for ' + name,
		height: 240,
		width: 800,
		backgroundColor: 'transparent',
		series: [{
				pointSize: 15
			},
		],
		pointShape: {
			type: 'star',
			sides: 5
		}
	};

	var chart = new google.visualization.ScatterChart(chartDiv);
	chartDiv.style.marginLeft = "50px";

	chart.draw(data, options);
	return chartDiv
}

function fetchJIRA(pmc, project, prepend) {
	if (project && project.length > 1) {
		GetAsyncJSON("/jiraversions.py?project=" + pmc + "&jiraname=" + project + "&prepend=" + prepend, null, function(json) {
			if (json && json.versions) {
				var n = 0;
				for (version in json.versions) {
					n++;
					jsdata.releases[pmc][version] = json.versions[version]
				}
				$('#dialog_' + pmc).dialog("close")
				var nproject = pmc
				alert("Fetched " + n + " releases from JIRA!")
				renderFrontPage(jsdata)

			} else {
				alert("Couldn't find any release data :(")
			}
		})
	}

}

function addRelease(pmc, version, date) {
	if (version && version.length > 1 && date.match(/^(\d\d\d\d)-(\d\d)-(\d\d)$/)) {
		var x = date.split("-");
		var y = new Date(x[0],parseInt(x[1])-1,parseInt(x[2]));
		var nn = parseInt(y.getTime()/1000);
		GetAsyncJSON("/addrelease.py?json=true&committee=" + pmc + "&version=" + escape(version) + "&date=" + nn, null, function(json) {
			if (json && json.versions) {
				var n = 0;
				for (version in json.versions) {
					n++;
					jsdata.releases[pmc][version] = json.versions[version]
				}
				$('#rdialog_' + pmc).dialog("close")
				var nproject = pmc
				alert("Release added!")
				renderFrontPage(jsdata)

			} else {
				alert("Couldn't add release data :(")
			}
		})
	}

}
