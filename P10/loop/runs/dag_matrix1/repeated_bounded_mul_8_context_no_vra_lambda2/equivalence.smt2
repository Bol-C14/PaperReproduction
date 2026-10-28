; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x650 (bvmul ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a)))) ((_ zero_extend 5) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b))))))))
(let ((?x161 ((_ extract 7 0) ?x650)))
(let (($x91 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x121 (ite $x91 ((_ extract 7 0) (bvadd ?x161 ?x161)) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))))
(let ((?x11 ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b))))))
(and (distinct (ite $x91 (bvadd ?x11 ?x11) c) ?x121) true)))))))
(check-sat)
