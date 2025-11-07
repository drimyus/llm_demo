(function ($) {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie('csrftoken');

  // Helpers to handle models that wrap output in Markdown code fences or return raw JSON as string
  function stripCodeFences(text) {
    if (typeof text !== 'string') return text;
    let t = text.trim();
    // Remove leading ```lang and trailing ``` if present
    if (t.startsWith('```')) {
      const firstNl = t.indexOf('\n');
      if (firstNl !== -1) t = t.slice(firstNl + 1);
      if (t.endsWith('```')) t = t.slice(0, -3);
    }
    return t.trim();
  }

  function parseMaybeJson(text) {
    if (typeof text !== 'string') return null;
    const t = stripCodeFences(text);
    try { return JSON.parse(t); } catch (_) {}
    const si = t.indexOf('{');
    const ei = t.lastIndexOf('}');
    if (si !== -1 && ei !== -1 && ei > si) {
      try { return JSON.parse(t.slice(si, ei + 1)); } catch (_) {}
    }
    return null;
  }

  $(function () {
    const $form = $('#brief-form');
    const $btn = $('#submit');
    const $loading = $('#loading');
    const $result = $('#result');
    const $error = $('#error');

    function setLoading(isLoading) {
      if (isLoading) {
        $btn.prop('disabled', true);
        $loading.removeClass('hidden');
      } else {
        $btn.prop('disabled', false);
        $loading.addClass('hidden');
      }
    }

    $form.on('submit', function (e) {
      e.preventDefault();
      $error.addClass('hidden').empty();
      $result.addClass('hidden');
      setLoading(true);

      const payload = {
        brand: $('#brand').val().trim(),
        platform: $('#platform').val(),
        goal: $('#goal').val(),
        tone: $('#tone').val()
      };

      $.ajax({
        url: '/api/generate_brief',
        method: 'POST',
        data: JSON.stringify(payload),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': csrftoken },
      })
      .done(function (data) {
        // Normalize response in case server returned a string or brief contains fenced JSON
        let res = data;
        if (typeof res === 'string') {
          const parsed = parseMaybeJson(res);
          if (parsed) res = parsed; else res = { brief: stripCodeFences(res), angles: [], criteria: [], metrics: {} };
        }
        // If brief itself is a JSON string (model echoed entire object), try to parse it
        if (res && typeof res.brief === 'string' && res.brief.trim().startsWith('{')) {
          const inner = parseMaybeJson(res.brief);
          if (inner && (inner.brief || inner.angles || inner.criteria)) {
            res = Object.assign({}, res, inner);
          } else {
            res.brief = stripCodeFences(res.brief);
          }
        } else if (res && typeof res.brief === 'string') {
          res.brief = stripCodeFences(res.brief);
        }

        // Render result
        $('#brief-text').text(res.brief || '');

        const $angles = $('#angles-list').empty();
        (res.angles || []).forEach(function (a) {
          $angles.append($('<li>').text(a));
        });

        const $criteria = $('#criteria-list').empty();
        (res.criteria || []).forEach(function (c) {
          $criteria.append($('<li>').text(c));
        });

        const m = res.metrics || {};
        const usage = m.usage || {};
        $('#metrics').text(
          `Latency: ${m.latency_ms || 0} ms — Tokens: `+
          `${usage.total_tokens || 0} (prompt ${usage.prompt_tokens || 0}, completion ${usage.completion_tokens || 0})`
        );

        $result.removeClass('hidden');
      })
      .fail(function (xhr) {
        let msg = 'Something went wrong.';
        try {
          const res = JSON.parse(xhr.responseText);
          if (res.errors) {
            msg = Object.values(res.errors).join(' ');
          } else if (res.error) {
            msg = res.error;
          }
        } catch (_) {}
        $error.text(msg).removeClass('hidden');
      })
      .always(function () {
        setLoading(false);
      });
    });
  });
})(jQuery);
