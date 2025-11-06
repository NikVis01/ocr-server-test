Run two cooperating processes on the same machine:
	1.	VLM server (vLLM) for PaddleOCR-VL’s language decoding
paddlex_genai_server --model_name PaddleOCR-VL-0.9B --backend vllm --host 0.0.0.0 --port 8118 [--backend_config vllm_config.yaml]
	2.	Official Serving API for the full layout-parsing pipeline
paddlex --serve --pipeline PaddleOCR-VL --host 0.0.0.0 --port 8080
…and point the pipeline to your vLLM at http://127.0.0.1:8118/v1. In config files this is:
VLRecognition.genai_config.backend: vllm-server and server_url: http://127.0.0.1:8118/v1.
Why this topology? It’s the supported path to accelerate the VLM decode while retaining the official layout/table/formula pipeline and the clean /layout-parsing API. (Direct PaddlePaddle inference is possible, but it requires >= CC 8.5 and is slower; a pure vLLM OpenAI-style endpoint alone won’t perform the layout work.)


from pathlib import Path
from paddleocr import PaddleOCRVL

input_file = "./your_pdf_file.pdf"
output_path = Path("./output")

pipeline = PaddleOCRVL(vl_rec_backend="vllm-server", vl_rec_server_url="{LYCEUM_PADDLE_SERVER}")
output = pipeline.predict(input=input_file)

markdown_list = []
markdown_images = []

for res in output:
    md_info = res.markdown
    markdown_list.append(md_info)
    markdown_images.append(md_info.get("markdown_images", {}))

markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)

mkd_file_path = output_path / f"{Path(input_file).stem}.md"
mkd_file_path.parent.mkdir(parents=True, exist_ok=True)

with open(mkd_file_path, "w", encoding="utf-8") as f:
    f.write(markdown_texts)

for item in markdown_images:
    if item:
        for path, image in item.items():
            file_path = output_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(file_path)


pipeline_name: PaddleOCR-VL

batch_size: 64

use_queues: True

use_doc_preprocessor: False
use_layout_detection: True
use_chart_recognition: False
format_block_content: False

SubModules:
  LayoutDetection:
    module_name: layout_detection
    model_name: PP-DocLayoutV2
    model_dir: null
    batch_size: 8
    threshold:
      0: 0.5 # abstract
      1: 0.5 # algorithm
      2: 0.5 # aside_text
      3: 0.5 # chart
      4: 0.5 # content
      5: 0.4 # formula
      6: 0.4 # doc_title
      7: 0.5 # figure_title
      8: 0.5 # footer
      9: 0.5 # footer
      10: 0.5 # footnote
      11: 0.5 # formula_number
      12: 0.5 # header
      13: 0.5 # header
      14: 0.5 # image
      15: 0.4 # formula
      16: 0.5 # number
      17: 0.4 # paragraph_title
      18: 0.5 # reference
      19: 0.5 # reference_content
      20: 0.45 # seal
      21: 0.5 # table
      22: 0.4 # text
      23: 0.4 # text
      24: 0.5 # vision_footnote
    layout_nms: True
    layout_unclip_ratio: [1.0, 1.0]
    layout_merge_bboxes_mode:
      0: "union" # abstract
      1: "union" # algorithm
      2: "union" # aside_text
      3: "large" # chart
      4: "union" # content
      5: "large" # display_formula
      6: "large" # doc_title
      7: "union" # figure_title
      8: "union" # footer
      9: "union" # footer
      10: "union" # footnote
      11: "union" # formula_number
      12: "union" # header
      13: "union" # header
      14: "union" # image
      15: "large" # inline_formula
      16: "union" # number
      17: "large" # paragraph_title
      18: "union" # reference
      19: "union" # reference_content
      20: "union" # seal
      21: "union" # table
      22: "union" # text
      23: "union" # text
      24: "union" # vision_footnote
  VLRecognition:
    module_name: vl_recognition
    model_name: PaddleOCR-VL-0.9B
    model_dir: null
    batch_size: 2048
    genai_config:
      backend: vllm-server #native
      server_url: http://0.0.0.0:8118/v1

SubPipelines:
  DocPreprocessor:
    pipeline_name: doc_preprocessor
    batch_size: 8
    use_doc_orientation_classify: True
    use_doc_unwarping: True
    SubModules:
      DocOrientationClassify:
        module_name: doc_text_orientation
        model_name: PP-LCNet_x1_0_doc_ori
        model_dir: null
        batch_size: 8
      DocUnwarping:
        module_name: image_unwarping
        model_name: UVDoc
        model_dir: null

Serving:
  extra:
    max_num_input_imgs: null





