function downloadCSV(isAdmin) {
    // Init CSV array.
    var csv = [
            ['data:text/csv;charset=utf-8,DATE,LOCATION,NUMBER OF AUTOMOBILES,NUMBER OF BICYCLES,' +
            'NUMBER OF PEDESTRIANS,DESCRIPTION,INJURIES,INJURIES DESCRIPTION,DEATHS,LICENSE PLATES,PICTURE URL']
    ];
    if (isAdmin) {
        csv[0] = csv[0] + ',CONTACT NAME';
        csv[0] = csv[0] + ',CONTACT PHONE';
        csv[0] = csv[0] + ',CONTACT EMAIL';
    }
    markersDisplayedOnMap.forEach(function(marker) {
        var licensePlates = marker.licensePlates.split(',').join(';');

        var line = [marker.incidentDate, marker.locationName, marker.automobileNum,
                    marker.bicycleNum, marker.pedestrianNum, marker.description, marker.injuries,
                    marker.injuries_description, marker.deaths, marker.licensePlates, marker.pictureUrl];
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
