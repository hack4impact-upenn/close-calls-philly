function downloadCSV(isAdmin) {
    // Init CSV array.
    var csv = [
            ['data:text/csv;charset=utf-8,DATE,LOCATION,PEDESTRIAN NUMBER,AUTOMOBILE NUMBER,' + 
            'BICYCLE NUMBER,OTHER NUMBER,DESCRIPTION,INJURIES,LICENSE PLATES,PICTURE URL']
    ];
    if (isAdmin) {
        csv[0] = csv[0] + ',CONTACT NAME';
        csv[0] = csv[0] + ',CONTACT PHONE';
        csv[0] = csv[0] + ',CONTACT EMAIL';
    }
    markersDisplayedOnMap.forEach(function(marker) {
        var license_plates = marker.license_plates.split(',').join(';');
        var line = [marker.incidentDate, marker.locationName, marker.pedestrianNum,
                    marker.automobileNum, marker.bicycleNum, marker.otherNum,
                    marker.description, marker.injuries, license_plates,
                    marker.pictureUrl];
        if (isAdmin) {
            line.push(marker.contactName);
            line.push(marker.contactPhone);
            line.push(marker.contactEmail);
        }

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
