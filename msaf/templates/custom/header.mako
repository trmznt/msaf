
    <!-- navbar -->
    <div class="navbar navbar-fixed-top navbar-inverse">
      <div class="navbar-inner">
        <div class="container">

          <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </a>

          <div class="nav-collapse">
            <ul class="nav">
              <li class="active"><a href="/">Home</a></li>
              <li><a href="#about">About</a></li>
              <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                    Explore Data <b class="caret"></b></a>
                  <ul class="dropdown-menu">
                    <li><a href="/batch">Batch</a></li>
                    <li><a href="/sample">Sample</a></li>
                    <li><a href="/location">Region</a></li>
                    <li><a href="/markerset">Marker Set</a></li>
                    <li><a href="#">Subject</a></li>
                  </ul>
              </li>
              <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                    Analyse Data <b class="caret"></b></a>
                  <ul class="dropdown-menu">
                    <li><a href="/queryset">Query Wizard</a></li>
                    <li><a href="/analysis/allele">Allele Summary</a></li>
                    <li><a href="/analysis/moi">Multiplicity of Infection</a></li>
                    <li><a href="#">LD</a></li>
                    <li><a href="/analysis/genotype">Genotype Summary</a></li>
                    <li><a href="/analysis/phylogenetics">Phylogenetics</a></li>
                    <li><a href="/analysis/pca">PCA</a></li>
                    <li><a href="/analysis/predefined">Predefined Analysis</a></li>
                  </ul>
              </li>
              <li><a href="/upload">Upload Data</a></li>
              <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                    Digital Assets <b class="caret"></b></a>
                  <ul class="dropdown-menu">
                    <li><a href="#">Protocols</a></li>
                    <li><a href="#">Articles</a></li>
                    <li><a href="#">Ethics</a></li>
                    <li><a href="#">Working papers</a></li>
                  </ul>
              </li>

            </ul>
            <div class="pull-right">
            <ul class="nav">
              <li><a href="/mgr">Manager</a></li>
              <li>${userlink()}</li>
            </ul>
            <a class="brand" href="#">MsAF</a>
            </div>
          </div><!--/.nav-collapse -->
        </div>
      </div>
    </div>
    <!-- /navbar -->

##
##
<%def name="userlink()">
% if request.authenticated():
    <a href="#"><i class="icon-white icon-user"></i> ${request.userinstance().login}</a>
% else:
    <a href="#"><i class="icon-white icon-user"></i> Anonymous</a>
% endif
</%def>

