function expandImage(download) {
    var imageContainer = event.target.parentNode.closest('.image');
    var imageUrl = imageContainer.querySelector('img').src;

    var expandedImage = document.createElement('div');
    expandedImage.className = 'expanded-image';

    var imageWrapper = document.createElement('div');
    imageWrapper.className = 'image-wrapper';

    var image = document.createElement('img');
    image.src = imageUrl;
    image.onload = function() {
      var downloadButton = document.createElement('a');
      downloadButton.href = imageUrl;
      downloadButton.download = 'image.jpg';
      downloadButton.className = 'download-button';
      downloadButton.innerText = 'Tải ảnh về';

      imageWrapper.appendChild(image);
      if (download){
          imageWrapper.appendChild(downloadButton);
      }
      expandedImage.appendChild(imageWrapper);

      expandedImage.onclick = function() {
        this.remove();
      };

      document.body.appendChild(expandedImage);
    };
  }