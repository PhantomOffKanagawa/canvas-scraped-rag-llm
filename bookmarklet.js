function downloadURL(url, filename) {
    fetch(url)
      .then(response => response.blob())
      .then(blob => {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    })
  }
  function downloadJSON(obj, filename) {
    
      const link = document.createElement("a");
      link.href = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(obj, null, 4));
      link.download = filename;
      link.click();
    
  }
  const questions = $(".question").map((i, q) => ({
      question: $(q).find("div.question_text").html().trim(),
      image: $(q).find(".question_text img").attr("src") || null,
      answers: $(q).find(".select_answer.answer_type").map((j, a) => ({
          correct: $(a).find(".question_input").is(':checked'),
          content: $(a).find(".answer_text").text() || $(a).find(".answer_html").html()
      })).get()
  })).get();
  /*questions.map((x, i) => {
      if(x.image) {
          downloadURL(x.image, `quiz_${quiz}_question_${i + 1}.png`);
          x.image = `quiz_${quiz}_question_${i + 1}.png`
      }
      return x;
  });*/
  downloadJSON(questions, `quiz_${document.getElementById("quiz_title").innerHTML.trim().replace(" ", "_")}.json`);