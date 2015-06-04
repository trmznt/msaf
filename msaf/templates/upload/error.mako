<%inherit file="rhombus:templates/base.mako" />


<h2>Error</h2>

<p>The submitted CSV/JSON file contains errors and inconsistency as reported from the log below:</p>

<pre>
${report_log}
</pre>

<p>Please corrent the input file and resubmit the file</p>

