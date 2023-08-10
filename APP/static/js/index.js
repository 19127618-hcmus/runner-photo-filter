function previewImage(event) {
    var input = event.target;
    var reader = new FileReader();
    reader.onload = function () {
        var preview = document.getElementById('preview');
        preview.src = reader.result;
        preview.classList.remove('d-none');
        preview.classList.add('mb-2');
    };
    reader.readAsDataURL(input.files[0]);
}


const searchMethodButtons = document.querySelectorAll('input[name="search_method"]');

searchMethodButtons.forEach(function(button) {
    button.onclick = function() {
        var bibField = document.getElementById("bib_field");
        var imageField = document.getElementById("image_field");
        var submitBtn = document.getElementById("submit-button");
        var submitBtnOr = document.getElementById("submit-button-or");
        var text = document.getElementById("gen-text");
        var inputImage = document.getElementById("image");
        var imageFieldSmBtn = document.getElementById("uploadImageBtn");

        bibField.classList.add("d-none");
        imageField.classList.add("d-none");
        imageFieldSmBtn.classList.add("d-none");
        submitBtnOr.classList.add("d-none");
        submitBtn.classList.add("d-none");

        document.getElementById("bib").value = "";
        document.getElementById("image").value = null;
        document.getElementById("preview").classList.add('d-none');

        var fileError = document.getElementById('main-form-error');
        fileError.style.display = "none"

        // Lấy giá trị (value) của nút ấn được nhấp vào
        const selectedSearchMethod = button.value;

        if (selectedSearchMethod === "bib") {
            bibField.classList.remove("d-none");
            submitBtn.classList.remove("d-none");
            text.innerHTML = "Nhập vào số bib cần tìm"
        } else if (selectedSearchMethod === "face") {
            text.innerHTML = "Tải lên ảnh chứa khuôn mặt cần tìm"
            inputImage.disabled = false;
            imageField.classList.remove("d-none");
            imageFieldSmBtn.classList.remove("d-none");
        } else if (selectedSearchMethod === "both") {
            text.innerHTML = "Nhập vào ít nhất một trong 2 thông tin, số bib hoặc khuôn mặt cần tìm"
            bibField.classList.remove("d-none");
            imageField.classList.remove("d-none");
            submitBtnOr.classList.remove("d-none");
            inputImage.disabled = false;
        }
        else if (selectedSearchMethod === "and") {
            text.innerHTML = "Nhập vào cả 2 thông tin, số bib và tải lên khuôn mặt cần tìm"
            bibField.classList.remove("d-none");
            imageField.classList.remove("d-none");
            imageFieldSmBtn.classList.remove("d-none");
        }

    };
});



function handleImageChange(event) {
    var fileInput = document.getElementById('image');
    var fileError = document.getElementById('main-form-error');
    fileError.textContent = "Hãy nhập vào ảnh của vận động viên cần tìm"
    
    if (fileInput.files.length > 0) {
        fileError.style.display = 'none';
    } else {
        fileError.style.display = 'block';
    }
    
    previewImage(event);
}

function uploadImage() {
    var formData = new FormData();
    var imageFile = document.getElementById("image").files[0];
    formData.append("image", imageFile);

    $("#imageModal").modal("hide"); // Hide the modal

    $("#loadingIndicator").show(); // Show loading indicator

    $.ajax({
        url: "/upload_image",
        type: "POST",
        data: formData,
        contentType: false,
        processData: false,
        success: function (response) {
            displayFacesAsOptions(response.faces);
            $("#loadingIndicator").hide(); // Hide loading indicator
            $("#startSearchBtn").show(); // Show the start search button
        },
        error: function (error) {
            console.log(error);
            $("#loadingIndicator").hide(); // Hide loading indicator
            $("#startSearchBtn").show(); // Show the start search button
        }
    });
}


function displayFacesAsOptions(faceImages) {
    var modalImage = document.getElementById("modalImage");
    modalImage.innerHTML = "";

    if (faceImages.length < 1) {
        var imageErr = document.createElement("h3");
        imageErr.textContent = "Không tìm thấy khuôn mặt";
        modalImage.appendChild(imageErr);
    }
    else{
        document.getElementById("submitBtn-modal").disabled = false;
    }

    faceImages.forEach(function (faceImage) {
        var imageOption = document.createElement("div");
        imageOption.classList.add("image-option", "col-md-2");

        var imageLabel = document.createElement("label");
        imageLabel.classList.add("select-face");
        imageLabel.htmlFor = faceImage;
        imageLabel.onclick = function () {
            selectImage(this);
        };

        var imageInput = document.createElement("input");
        imageInput.type = "radio";
        imageInput.name = "selected_image";
        imageInput.value = faceImage;
        imageInput.style.display = "none";

        var imageElement = document.createElement("img");
        imageElement.classList.add("select-face");
        imageElement.src = faceImage;
        imageElement.alt = "Face";

        imageLabel.appendChild(imageInput);
        imageLabel.appendChild(imageElement);
        imageOption.appendChild(imageLabel);
        modalImage.appendChild(imageOption);
    });
}


var selectedImage = null;

function selectImage(imageOption) {
    if (selectedImage) {
        selectedImage.classList.remove("selected-image");
    }

    selectedImage = imageOption;
    selectedImage.classList.add("selected-image");

    var imageRadio = selectedImage.querySelector('input[type="radio"]');
    imageRadio.checked = true;

    console.log('inin')
    document.getElementById('none-face-selected').style.display = 'none';

}

function clearModalContent() {
    var modalContent = document.getElementById("modalImage");
    modalContent.innerHTML = "";
}
document.getElementById("uploadImageBtn").addEventListener("click", function () {
    var bibInput = document.getElementById('bib');
    var fileInput = document.getElementById('image');
    var fileError = document.getElementById('main-form-error');
    var method = document.querySelector('input[name=search_method]:checked').value;
    if (method == 'and'){
        fileError.textContent = "Hãy nhập vào số bib và ảnh của vận động viên cần tìm";
        if (fileInput.files.length === 0 || bibInput.value.trim().length <= 0) {
            fileError.style.display = 'block';
        } else {
            fileError.style.display = 'none';
            $(imageModal).modal('show');
            uploadImage();
        }
    }
    else{
        fileError.textContent = "Hãy nhập vào ảnh của vận động viên cần tìm";
    

        const uploadImageBtn = document.getElementById('uploadImageBtn');
        const imageModal = document.getElementById('imageModal');

        if (fileInput.files.length === 0) {
            fileError.style.display = 'block';
        } else {
            fileError.style.display = 'none';
            $(imageModal).modal('show');
            uploadImage();
        }
    }
    clearModalContent()
});

document.getElementById("tryAgain-modal").addEventListener("click", function () {
    document.getElementById("image").value = null;
    document.getElementById("preview").classList.add('d-none');
    clearModalContent()
    $('#imageModal').modal('hide');
});

document.getElementById("searchForm").addEventListener("submit", function (event) {
    var selectedImageRadio = document.querySelector('input[name="selected_image"]:checked');
    if (selectedImageRadio) {
        var selectedImageValue = selectedImageRadio.value;
        var selectedImageHiddenInput = document.createElement("input");
        selectedImageHiddenInput.type = "hidden";
        selectedImageHiddenInput.name = "selected_image";
        selectedImageHiddenInput.value = selectedImageValue;
        this.appendChild(selectedImageHiddenInput);
    }
});


document.getElementById("submitBtn-modal").addEventListener("click", function () {
    var faceError = document.getElementById("none-face-selected");
    

    if(document.querySelector('input[name="selected_image"]:checked') == null){
        faceError.style.display = 'block';
        
    }
    else{
        faceError.style.display = 'none';
        var selectedImage = document.querySelector('input[name="selected_image"]:checked').value;
        var seleced_image = document.getElementById("selected_image") .value = selectedImage;
        document.getElementById("searchForm").submit();
    }

});

// 