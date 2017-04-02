function downloadCSV(isAdmin) {
    // Init CSV array.
    var csv;
    if (isAdmin) {
        csv = [
            ['data:text/csv;charset=utf-8,DATE,LOCATION,PEDESTRIAN NUMBER,AUTOMOBILE NUMBER,' + 
            'BICYCLE NUMBER,OTHER NUMBER,DESCRIPTION,INJURIES,PICTURE URL,CONTACT NAME,' + 
            'CONTACT PHONE,CONTACT EMAIL']
    ];
    } else {
        console.log("no admin columns");
        csv = [
            ['data:text/csv;charset=utf-8,DATE,LOCATION,PEDESTRIAN NUMBER,AUTOMOBILE NUMBER,' + 
            'BICYCLE NUMBER,OTHER NUMBER,DESCRIPTION,INJURIES,PICTURE URL']
        ];
    }
    markersDisplayedOnMap.forEach(function(marker) {
        var line;
        if (isAdmin) {
            line = [marker.incidentDate, marker.locationName, marker.pedestrianNum,
                    marker.automobileNum, marker.bicycleNum, marker.otherNum,
                    marker.description, marker.injuries, marker.pictureUrl,
                    marker.contactName, marker.contactPhone, marker.contactEmail];
        } else {
            line = [marker.incidentDate, marker.locationName, marker.pedestrianNum,
                    marker.automobileNum, marker.bicycleNum, marker.otherNum,
                    marker.description, marker.injuries, marker.pictureUrl];
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
