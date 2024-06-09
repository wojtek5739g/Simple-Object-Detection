use pyo3::prelude::*;
use std::io::{self, BufRead};
use std::fs;
use std::env;
use std::sync::Arc;
use std::path::Path;

use itertools::izip;
use opencv::{core, dnn, imgcodecs, imgproc, prelude::*};
use rayon::prelude::*;

fn load_class_names(names_path: &str) -> anyhow::Result<Vec<String>> {
    let file = fs::File::open(names_path)?;
    let reader = io::BufReader::new(file);
    let mut class_names = Vec::new();
    for line in reader.lines() {
        class_names.push(line?);
    }
    Ok(class_names)
}

#[pyfunction]
fn object_detection(folder_path: &str) -> PyResult<Vec<(String, Vec<String>)>>{
    let current_dir = env::current_dir()?;
    
    println!("Current working directory: {:?}", current_dir);

    let config = current_dir.join("model/yolov4-tiny.cfg");
    let weights = current_dir.join("model/yolov4-tiny.weights");
    let names = current_dir.join("model/coco.names");

    let config_str = config.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::Other, "Invalid config path"))?.replace('\\', "/");
    let weights_str = weights.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::Other, "Invalid weights path"))?.replace('\\', "/");
    let names_str = names.to_str().ok_or_else(|| io::Error::new(io::ErrorKind::Other, "Invalid names path"))?.replace('\\', "/");

    let class_names = load_class_names(&names_str)?;
    let class_names = Arc::new(class_names); 

    let path = fs::read_dir(folder_path).unwrap();

    let img_paths: Vec<_> = path.filter_map(|entry| {
        let entry = entry.ok()?;
        if entry.metadata().ok()?.is_file() {
            Some(entry.path().to_string_lossy().replace('\\', "/"))
        } else {
            None
        }
    }).collect();

    // Parallelism
    let results: Vec<(String, Vec<String>)> = img_paths.par_iter().map(|img_path_str| {
        match process_image(img_path_str, &weights_str, &config_str, &class_names) {
            Ok(objects) => (img_path_str.clone(), objects),
            Err(e) => {
                eprintln!("Error processing image {}: {:?}", img_path_str, e);
                (img_path_str.clone(), Vec::new())
            }
        }
    }).collect();

    Ok(results)
}

fn process_image(img_path_str: &str, weights_str: &str, config_str: &str, class_names: &Arc<Vec<String>>) -> anyhow::Result<Vec<String>> {
    println!("Img_path_str: {}", img_path_str);

    let net = dnn::read_net(&weights_str, &config_str, "Darknet")?;
    let mut model = dnn::DetectionModel::new_1(&net)?;
    let scale: f64 = 1.0 / 255.0;
    let size = core::Size {
        width: 416,
        height: 416,
    };

    let mean = core::Scalar {
        0: [0.0, 0.0, 0.0, 0.0], // Generally for YOLO
    };

    let swap_rb: bool = true;
    let crop: bool = false;
    model.set_input_params(scale, size, mean, swap_rb, crop)?;

    let mut class_ids = core::Vector::<i32>::new();
    let mut confidences = core::Vector::<f32>::new();
    let mut boxes = core::Vector::<core::Rect>::new();

    let img = imgcodecs::imread_def(&img_path_str)?;

    let mut resized_img = Mat::default();
    imgproc::resize(
        &img,
        &mut resized_img,
        core::Size {
            width: 416,
            height: 416,
        },
        0.0,
        0.0,
        imgproc::INTER_LINEAR,
    )?;

    model.detect_def(&resized_img, &mut class_ids, &mut confidences, &mut boxes)?;

    // Put bounding boxes on the img
    let color = core::Scalar {
        0: [0.0, 140.0, 255.0, 0.0], // Orange
    };

    let mut detected_objects = Vec::new();
    for (cid, _cf, b) in izip!(&class_ids, &confidences, &boxes) {
        imgproc::rectangle_def(&mut resized_img, b, color)?;

        let label = &class_names[cid as usize];
        detected_objects.push(label.clone());
        let label_size = imgproc::get_text_size(label, imgproc::FONT_HERSHEY_SIMPLEX, 0.5, 1, &mut 0)?;
        let label_origin = core::Point::new(b.x, b.y - label_size.height);

        imgproc::put_text(
            &mut resized_img,
            label,
            label_origin,
            imgproc::FONT_HERSHEY_SIMPLEX,
            0.5,
            core::Scalar::new(255.0, 0.0, 0.0, 0.0),
            2,
            imgproc::LINE_8,
            false,
        )?;
    }

    let after_last_slash: Option<String>;
    let before_last_slash: Option<String>;

    if let Some(index) = img_path_str.rfind('/') {
        before_last_slash = Some(img_path_str[..index].to_string());
        after_last_slash = Some(img_path_str[index + 1..].to_string());
    } else {
        before_last_slash = None;
        after_last_slash = None;
    }

    if let Some(substring) = &after_last_slash {
        println!("After last slash: {}", substring);
    } else {
        println!("No '/' found in the string.")
    }

    if let Some(substring) = &before_last_slash {
        println!("Before last slash: {}", substring);
    } else {
        println!("No '/' found in the string.")
    }

    let output_dir = match &before_last_slash {
        Some(before) => before.clone() + "/outputs",
        None => "/output".to_string(),
    };

    if !Path::new(&output_dir).exists() {
        match fs::create_dir_all(&output_dir) {
            Ok(_) => println!("Successfully created directory: {}", output_dir),
            Err(e) => eprintln!("Failed to create directory: {}. Error: {}", output_dir, e),
        }
    } else {
        println!("Directory already exists: {}", output_dir);
    }

    let output_file_path = match &after_last_slash {
        Some(after) => format!{"{}/{}", output_dir, after},
        None => output_dir.clone(),
    };

    println!("Output file path: {}", &output_file_path);

    let params = core::Vector::new();
    let _ = imgcodecs::imwrite(&output_file_path, &resized_img, &params);
        
    
    Ok(detected_objects)
}

#[pymodule]
fn my_maturin_library(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(object_detection, m)?)?;
    Ok(())
}