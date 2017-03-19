// Init CSV array.
var csv = [
  ['data:text/csv;charset=utf-8,DATE,LOCATION,VEHICLE ID,DURATION,LICENSE PLATE,DESCRIPTION']
];

function downloadCSV() {
	console.log('here');
	markersDisplayedOnMap.forEach(function(marker) {
		var line = [marker.incidentDate, marker.locationName, marker.vehicleID,
				    marker.duration, marker.licensePlate, marker.description];
		csv.push(line.join(','));
	});
	var csvString = csv.join('\n');

	var encodedUri = encodeURI(csvString);
	var link = document.createElement("a");
	link.setAttribute("href", encodedUri);
	link.setAttribute("download", "my_data.csv");
	document.body.appendChild(link); // Required for FF

	// Download the data file.
	link.click();
}