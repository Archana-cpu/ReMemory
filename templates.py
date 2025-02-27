# templates.py

base_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{{ title }}</title>
  <!-- Google Fonts et Bootstrap pour un design moderne -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <!-- Ajout de Font Awesome pour les icônes -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" 
        integrity="sha512-Fo3rlrZj/k7ujTTXABVqCpM/I7MZSmU+FiScgB/suh1zZK0p9D3w1s59+d+KfQ/NTqqlBS+iQ1I/qWl8URF91g==" 
        crossorigin="anonymous" referrerpolicy="no-referrer" />
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background-color: #f7f7f8;
      color: #333;
      margin: 0;
      padding: 0;
    }
    body.dark-mode {
      background-color: #343541;
      color: #D1D5DB;
    }
    .navbar {
      border-bottom: 1px solid #e0e0e0;
    }
    body.dark-mode .navbar {
      border-bottom: 1px solid #444;
    }
    /* Centrage du titre dans la navbar */
    .navbar .container {
      position: relative;
    }
    .navbar-brand {
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
    }
    /* Styles de la sidebar */
    .sidebar {
      height: 100%;
      width: 250px;
      position: fixed;
      top: 0;
      left: -250px;
      background-color: #333;
      overflow-x: hidden;
      transition: 0.5s;
      padding-top: 60px;
      z-index: 1;
    }
    .sidebar.active {
      left: 0;
    }
  </style>
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      const darkModeToggle = document.getElementById("darkModeToggle");
      if (localStorage.getItem("darkMode") === "enabled") {
        document.body.classList.add("dark-mode");
        if (darkModeToggle) darkModeToggle.checked = true;
      }
    });
    function toggleDarkMode(checkbox) {
      if (checkbox.checked) {
        document.body.classList.add("dark-mode");
        localStorage.setItem("darkMode", "enabled");
      } else {
        document.body.classList.remove("dark-mode");
        localStorage.setItem("darkMode", "disabled");
      }
    }
    // Fonction globale pour toggler la sidebar
    function toggleSidebar() {
      var sidebar = document.getElementById("sidebar");
      if (sidebar) {
        sidebar.classList.toggle("active");
      }
    }
  </script>
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container">
      <a class="navbar-brand" href="#">
        <img src="{{ url_for('static', filename='images/app_icon.png') }}" alt="Icône" style="width:30px; vertical-align:middle;"> 
        ReMemory Chat
      </a>
      <ul class="navbar-nav ml-auto">
        {% if session.username %}
          <li class="nav-item"><a class="nav-link" href="{{ url_for('chat') }}">Chat</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('images') }}">Images</a></li>
          <li class="nav-item"><a class="nav-link" href="{{ url_for('logout_route') }}">Déconnexion</a></li>
          <li class="nav-item">
            <div class="form-check form-switch mt-2 ml-3">
              <input class="form-check-input" type="checkbox" id="darkModeToggle" onchange="toggleDarkMode(this)">
              <label class="form-check-label" for="darkModeToggle">Mode Nuit</label>
            </div>
          </li>
        {% endif %}
      </ul>
    </div>
  </nav>
  <div class="container-fluid p-0 mt-2">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="alert alert-info m-2">{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </div>
  <!-- jQuery 3.7.1 complet -->
  <script src="https://code.jquery.com/jquery-3.7.1.min.js" integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo=" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
"""

login_template = """
{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-center align-items-center" style="height: 80vh;">
  <div class="card p-4" style="min-width: 300px;">
    <h2 class="text-center mb-4">
      <img src="{{ url_for('static', filename='images/app_icon.png') }}" alt="Icône" style="width:40px; vertical-align:middle;">
      ReMemory Chat
    </h2>
    <form method="post" action="{{ url_for('login') }}">
      <div class="form-group">
        <label for="username">Nom d'utilisateur</label>
        <input type="text" class="form-control" name="username" id="username" placeholder="Entrez votre nom d'utilisateur">
      </div>
      <button type="submit" class="btn btn-primary btn-block">Se connecter</button>
    </form>
  </div>
</div>
{% endblock %}
"""

chat_template = """
{% extends "base.html" %}
{% block content %}
<style>
  /* Styles pour le chat */
  .open-btn {
    position: fixed;
    left: 10px;
    top: 10px;
    font-size: 30px;
    cursor: pointer;
    z-index: 2;
    color: #333;
  }
  .chat-container {
    width: 100%;
    height: calc(100vh - 60px);
    display: flex;
    flex-direction: column;
    padding: 20px;
    background: #fff;
  }
  .chat-log {
    flex-grow: 1;
    overflow-y: auto;
    padding: 10px;
    background: #f3f3f3;
    border-radius: 8px;
    margin-bottom: 10px;
  }
  .message-container {
    display: flex;
    align-items: flex-start;
  }
  .justify-content-start {
    justify-content: flex-start;
  }
  .justify-content-end {
    justify-content: flex-end;
  }
  .message-bubble {
    max-width: 70%;
    padding: 10px 15px;
    border-radius: 18px;
    margin: 0 10px;
  }
  .assistant {
    background: #e5e5ea;
    color: #000;
  }
  .user {
    background: #0b93f6;
    color: #fff;
  }
  .message-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
  }
  /* Styles personnalisés pour les boutons avec icônes */
  .btn-icon {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60px;
  }
  .btn-icon i {
    font-size: 24px;
  }
  .btn-icon span {
    font-size: 12px;
    margin-top: 5px;
  }
</style>

<!-- Bouton pour afficher la sidebar -->
<span class="open-btn" onclick="toggleSidebar()">☰</span>

<!-- Sidebar multimédia personnalisée -->
<div id="sidebar" class="sidebar">
  <a href="javascript:void(0)" class="close-btn" onclick="toggleSidebar()">×</a>
  <h5 style="color: #f1f1f1; padding-left: 32px;">Multimédia</h5>
  <div style="padding: 10px 32px; color: #f1f1f1;">
    <form method="post" action="{{ url_for('upload_image') }}" enctype="multipart/form-data">
      <div class="form-group">
        <label for="sidebar_image" style="color: #f1f1f1;">Image</label>
        <input type="file" class="form-control-file" name="image" id="sidebar_image" required>
      </div>
      <button type="submit" class="btn btn-secondary btn-block btn-icon" title="Analyser l'image">
        <i class="fas fa-image"></i>
        <span>Analyser</span>
      </button>
    </form>
    <hr style="border-color: #555;">
    <div id="recorder" class="mt-3">
      <button id="startRecording" class="btn btn-secondary btn-block btn-icon" title="Démarrer l'enregistrement">
        <i class="fas fa-microphone"></i>
        <span>Démarrer</span>
      </button>
      <button id="stopRecording" class="btn btn-secondary btn-block btn-icon" disabled title="Arrêter l'enregistrement">
        <i class="fas fa-stop"></i>
        <span>Arrêter</span>
      </button>
      <audio id="audioPlayback" controls class="w-100 mt-2"></audio>
      <button id="sendAudio" class="btn btn-primary btn-block btn-icon mt-2" disabled title="Envoyer l'audio">
        <i class="fas fa-paper-plane"></i>
        <span>Envoyer</span>
      </button>
    </div>
  </div>
</div>

<div class="main-content">
  <div class="chat-container">
    <div class="chat-header mb-2">
      <h4>Connecté en tant que: <span style="color: blue; font-weight: bold;">{{ username }}</span></h4>
      {% if session.image_mode %}
      <div class="alert alert-warning">
        <strong style="color: red;">Vous êtes en mode image.</strong> Tous vos messages seront ajoutés à la description de l'image en cours.
        <a href="{{ url_for('clear_image') }}" class="btn btn-sm btn-secondary">Quitter le mode image</a>
      </div>
      {% endif %}
    </div>
    <div class="chat-log" id="chatLog">
      {% for msg in chat_history %}
      <div class="message-container d-flex {% if msg.role == 'assistant' %}justify-content-start{% else %}justify-content-end{% endif %} mb-2">
        {% if msg.role == 'assistant' %}
          <img src="{{ url_for('static', filename='images/ai.png') }}" alt="IA" class="message-icon">
        {% endif %}
        <div class="message-bubble {% if msg.role == 'assistant' %}assistant{% else %}user{% endif %}">
          {{ msg.content|safe }}
        </div>
        {% if msg.role != 'assistant' %}
          <img src="{{ url_for('static', filename='images/human.png') }}" alt="Utilisateur" class="message-icon">
        {% endif %}
      </div>
      {% endfor %}
    </div>
    <div id="loadingIndicator" style="display:none; text-align: center; margin-bottom: 10px;">
      <div class="spinner-border text-primary" role="status">
        <span class="sr-only">Chargement...</span>
      </div>
      <span style="font-weight: bold; color: blue;"> Traitement en cours...</span>
    </div>
    <form id="chatForm">
      <div class="input-group">
        <input type="text" class="form-control" name="message" placeholder="Écrire un message..." required id="userMessage">
        <div class="input-group-append">
          <button type="submit" class="btn btn-primary"><span style="font-size: 18px;">📩</span></button>
        </div>
      </div>
      <div class="form-group form-check mt-2">
        <input type="checkbox" class="form-check-input" name="tts" id="tts" checked>
        <label class="form-check-label" for="tts">Activer la réponse vocale</label>
      </div>
    </form>
  </div>
</div>

{% endblock %}

{% block scripts %}
<script>
  $(document).ready(function(){
    // Gestion de la soumission du formulaire de chat via fetch en POST
    $("#chatForm").on("submit", function(e){
      e.preventDefault();
      const message = $("#userMessage").val().trim();
      if(message === ""){
        return;
      }
      // Affichage immédiat du message utilisateur
      $("#chatLog").append(
        '<div class="message-container d-flex justify-content-end mb-2">' +
          '<div class="message-bubble user">' + message + '</div>' +
          '<img src="{{ url_for("static", filename="images/human.png") }}" alt="Utilisateur" class="message-icon">' +
        '</div>'
      );
      $("#userMessage").val("");
      $("#loadingIndicator").show();
      // Envoyer la requête via fetch
      fetch('{{ url_for("chat") }}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, tts: $("#tts").is(":checked") })
      })
      .then(response => response.json())
      .then(data => {
        $("#chatLog").append(
          '<div class="message-container d-flex justify-content-start mb-2">' +
            '<img src="{{ url_for("static", filename="images/ai.png") }}" alt="IA" class="message-icon">' +
            '<div class="message-bubble assistant">' + data.reply + '</div>' +
          '</div>'
        );
        $("#loadingIndicator").hide();
      })
      .catch(error => {
        console.error("Erreur :", error);
        $("#loadingIndicator").hide();
      });
    });
    
    // Gestion du clic sur une image pour ouvrir le modal
    $(document).on("click", ".img-clickable", function(){
      var src = $(this).attr("src");
      console.log("Image cliquée, src:", src);
      if(src){
        $("#modalImage").attr("src", src);
        $("#imageModal").modal("show");
      } else {
        console.log("Source introuvable pour l'image cliquée.");
      }
    });
    
    // Gestion de l'enregistrement audio
    let mediaRecorder;
    let audioChunks = [];
    let audioBlob;
    
    const startBtn = $("#startRecording");
    const stopBtn = $("#stopRecording");
    const sendAudioBtn = $("#sendAudio");
    const audioPlayback = $("#audioPlayback");
    
    startBtn.on("click", async function(){
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        audioChunks = [];
        
        mediaRecorder.addEventListener("dataavailable", function(event) {
          if(event.data.size > 0){
            audioChunks.push(event.data);
          }
        });
        
        mediaRecorder.addEventListener("stop", function(){
          audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          const audioUrl = URL.createObjectURL(audioBlob);
          audioPlayback.attr("src", audioUrl);
          sendAudioBtn.prop("disabled", false);
        });
        
        startBtn.prop("disabled", true);
        stopBtn.prop("disabled", false);
      } catch (err) {
        console.error("Erreur lors de l'accès au micro :", err);
        alert("Impossible d'accéder au micro. Vérifiez vos permissions et réessayez.");
      }
    });
    
    stopBtn.on("click", function(){
      if(mediaRecorder && mediaRecorder.state !== "inactive"){
        mediaRecorder.stop();
        startBtn.prop("disabled", false);
        stopBtn.prop("disabled", true);
      }
    });
    
    sendAudioBtn.on("click", function(){
      let formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      fetch("{{ url_for('upload_audio') }}", {
        method: "POST",
        body: formData
      }).then(response => {
        window.location.reload();
      }).catch(err => {
        console.error("Erreur lors de l'envoi de l'audio :", err);
        alert("Erreur lors de l'envoi de l'audio.");
      });
      sendAudioBtn.prop("disabled", true);
    });
  });
</script>
{% endblock %}
"""

images_template = """
{% extends "base.html" %}
{% block content %}
<style>
  /* Carte horizontale avec image et contenu de même hauteur */
  .card-horizontal {
    display: flex;
    align-items: stretch;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    height: 220px; /* Hauteur fixe */
  }
  .card-horizontal .img-container {
    flex: 0 0 40%;
    height: 100%;
    position: relative;
  }
  .card-horizontal .img-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    cursor: pointer;
  }
  .card-horizontal .card-body {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
  }
  .tag-badge {
    display: inline-block;
    margin: 2px;
  }
</style>
<div class="container">
  <h3 class="text-center mb-4">Images uploadées de {{ username }}</h3>
  {% for card in cards %}
  <div class="card-horizontal">
    <div class="img-container">
      <!-- L'image cliquable -->
      <img src="{{ url_for('serve_image', filename=card.path[7:]) }}" alt="Image" class="img-clickable">
    </div>
    <div class="card-body">
      <h5 class="card-title">Description</h5>
      <p class="card-text">{{ card.description or "N/A" }}</p>
      <h6>Tags</h6>
      <p>
        {% if card.tags and card.tags|length > 0 %}
          {% for tag in card.tags %}
            <span class="badge badge-secondary tag-badge">{{ tag }}</span>
          {% endfor %}
        {% else %}
          <span class="badge badge-danger">Aucun tag généré</span>
        {% endif %}
      </p>
      <div class="mt-3">
        <a href="{{ url_for('play_description', index=loop.index0) }}" class="btn btn-primary btn-sm">Lire</a>
        <a href="{{ url_for('edit_image', index=loop.index0) }}" class="btn btn-info btn-sm">Modifier</a>
        <a href="{{ url_for('update_tags', index=loop.index0) }}" class="btn btn-warning btn-sm">Rafraîchir tags</a>
        <a href="{{ url_for('delete_image', index=loop.index0) }}" class="btn btn-danger btn-sm">Supprimer</a>
      </div>
    </div>
  </div>
  {% endfor %}
  <div class="text-center mt-3">
    <a href="{{ url_for('stop_tts') }}" class="btn btn-warning">Stop TTS</a>
    <a href="{{ url_for('images') }}" class="btn btn-secondary">Rafraîchir</a>
  </div>
</div>

<!-- Modal pour afficher l'image en grand -->
<div class="modal fade" id="imageModal" tabindex="-1" role="dialog" aria-labelledby="imageModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-lg" role="document">
    <div class="modal-content">
      <div class="modal-body p-0">
        <img id="modalImage" src="" alt="Grande image" style="width: 100%; height: auto;">
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Fermer</button>
      </div>
    </div>
  </div>
</div>

{% endblock %}

{% block scripts %}
<script>
  $(document).on("click", ".img-clickable", function(){
    var src = $(this).attr("src");
    console.log("Image cliquée, src:", src);
    if(src){
      $("#modalImage").attr("src", src);
      $("#imageModal").modal("show");
    } else {
      console.log("Source introuvable pour l'image cliquée.");
    }
  });
</script>
{% endblock %}
"""

edit_image_template = """
{% extends "base.html" %}
{% block content %}
<h3>Modifier l'image</h3>
<form method="post">
  <div class="form-group">
    <label for="description">Nouvelle description</label>
    <textarea class="form-control" name="description" id="description" rows="4">{{ image.description }}</textarea>
  </div>
  <div class="form-group">
    <label for="tags">Tags (séparés par des virgules)</label>
    <input type="text" class="form-control" name="tags" id="tags" value="{{ image.tags|join(', ') }}">
  </div>
  <button type="submit" class="btn btn-primary">Enregistrer</button>
  <a href="{{ url_for('images') }}" class="btn btn-secondary">Annuler</a>
</form>
{% endblock %}
"""

templates = {
  "base.html": base_template,
  "login.html": login_template,
  "chat.html": chat_template,
  "images.html": images_template,
  "edit_image.html": edit_image_template
}
