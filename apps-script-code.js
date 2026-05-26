function doPost(e) {
  var data = e.postData.contents;
  var json = JSON.parse(data);

  if (json.type === "log") {
    var user = json.user || "anonymous";
    var subject = "Converter log: " + (json.fileName || "unknown") + " from " + user + " (" + (json.version || "?") + ")";
    var body = "From: " + user + "\nFile: " + (json.fileName || "unknown") + "\nVersion: " + (json.version || "?") + "\nTime: " + (json.timestamp || "?") + "\n\n--- LOG ---\n" + (json.logText || "(empty)");
    GmailApp.sendEmail("pythonivelt@gmail.com", subject, body);
  } else {
    var fileName = json.fileName || "unknown";
    var brand = json.phoneBrand || "Unknown";
    var email = json.userEmail || "not provided";
    var subject = "New phone format: " + brand + " - " + fileName;
    var body = "Phone brand: " + brand + "\nContact email: " + email + "\nFile: " + fileName + "\n\nSee attached JSON.";
    var blob = Utilities.newBlob(data, "application/json", "report.json");
    GmailApp.sendEmail("pythonivelt@gmail.com", subject, body, {attachments: [blob]});
  }

  return ContentService.createTextOutput("{\"status\":\"ok\"}").setMimeType(ContentService.MimeType.JSON);
}
