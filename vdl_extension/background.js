chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "vdl_download",
    title: "Download with Kino 🎬",
    contexts: ["page", "link", "video"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "vdl_download") {
    let url = info.linkUrl || info.srcUrl || tab.url;
    if (url) {
      console.log("Sending URL to native host:", url);
      chrome.runtime.sendNativeMessage(
        'com.antigravity.vdl',
        { url: url },
        function(response) {
          if (chrome.runtime.lastError) {
            console.error("Native Messaging Error:", chrome.runtime.lastError.message);
            // We can't easily show an alert from a service worker, 
            // but the user will see if it fails (no terminal opens)
          } else {
            console.log("Response from host:", response);
          }
        }
      );
    }
  }
});
